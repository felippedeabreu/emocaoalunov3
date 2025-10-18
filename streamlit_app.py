import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(
    page_title="Análise de Emoções em Alunos",
    page_icon="📊",
    layout="wide"
)

# ---------------------------
# Constantes geográficas do ES
# ---------------------------
ES_CENTER = {"lat": -19.5, "lon": -40.5}
ES_BOUNDS = {
    "lat_min": -21.4, "lat_max": -18.0,
    "lon_min": -41.9, "lon_max": -39.0
}

# ---------------------------
# Funções utilitárias
# ---------------------------
@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normaliza lat/lon (se vierem como string com vírgula decimal)
    for col in ["lat", "lon"]:
        if col in df.columns and df[col].dtype == "object":
            df[col] = (
                df[col].astype(str)
                .str.replace(",", ".", regex=False)
                .str.extract(r"(-?\d+(?:\.\d+)?)")[0]
                .astype(float)
            )
    return df

def _guess_swap_and_sign(df: pd.DataFrame) -> (pd.DataFrame, dict):
    """
    Corrige problemas comuns:
    - longitude positiva (torna negativa)
    - latitudes positivas (torna negativas, já que ES está no hemisfério sul)
    - colunas trocadas (lat/ lon invertidas)
    Retorna df corrigido + contagem de correções para exibir ao usuário.
    """
    fixes = {"lon_neg": 0, "lat_neg": 0, "swapped": False}

    # Copiamos para não modificar original
    d = df.copy()

    # Se muitos lons > 0, inverta o sinal
    if (d["lon"] > 0).mean() > 0.6:
        d["lon"] = -d["lon"]
        fixes["lon_neg"] = int((df["lon"] > 0).sum())

    # Se muitas lats > 0, inverta o sinal
    if (d["lat"] > 0).mean() > 0.6:
        d["lat"] = -d["lat"]
        fixes["lat_neg"] = int((df["lat"] > 0).sum())

    # Heurística: se a média de |lon| ~ 20 e de |lat| ~ 40, provavelmente estão invertidas
    if d["lon"].abs().mean() < 30 and d["lat"].abs().mean() > 30:
        d[["lat", "lon"]] = d[["lon", "lat"]]
        fixes["swapped"] = True

    return d, fixes

def filter_es_bounds(df: pd.DataFrame) -> (pd.DataFrame, int):
    """Filtro por bounding box do ES."""
    mask = (
        (df["lat"].between(ES_BOUNDS["lat_min"], ES_BOUNDS["lat_max"])) &
        (df["lon"].between(ES_BOUNDS["lon_min"], ES_BOUNDS["lon_max"]))
    )
    removed = int((~mask).sum())
    return df.loc[mask].copy(), removed

@st.cache_data(show_spinner=False)
def load_geojson(path: str):
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def filter_by_geojson(df: pd.DataFrame, geojson_path: str) -> (pd.DataFrame, int):
    """
    Filtra pontos que estão dentro do polígono do ES usando shapely/geopandas.
    Requer geopandas; se não tiver, cai no filtro por bounding box.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point, shape

        gj = load_geojson(geojson_path)
        # Une todos os polígonos do GeoJSON em um único shape
        from shapely.ops import unary_union
        polys = []
        for feat in gj["features"]:
            polys.append(shape(feat["geometry"]))
        es_poly = unary_union(polys)

        gdf = gpd.GeoDataFrame(
            df.copy(),
            geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])],
            crs="EPSG:4326"
        )
        inside_mask = gdf.geometry.within(es_poly)
        removed = int((~inside_mask).sum())
        return gdf.loc[inside_mask].drop(columns="geometry").copy(), removed
    except Exception:
        # Fallback para bounding box
        return filter_es_bounds(df)

def center_from_df(df: pd.DataFrame) -> dict:
    if df.empty:
        return ES_CENTER
    return {"lat": float(df["lat"].mean()), "lon": float(df["lon"].mean())}

def add_common_filters(df: pd.DataFrame):
    col1, col2 = st.columns(2)
    with col1:
        emocao = st.selectbox("Filtrar por emoção:", ["Todas"] + sorted(df["dominante_emocao"].dropna().unique().tolist()))
    with col2:
        regiao = st.selectbox("Filtrar por região:", ["Todas"] + sorted(df["regiao"].dropna().unique().tolist()))
    if emocao != "Todas":
        df = df[df["dominante_emocao"] == emocao]
    if regiao != "Todas":
        df = df[df["regiao"] == regiao]
    return df

# ---------------------------
# Menu lateral
# ---------------------------
st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Escolha uma seção:",
    ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"]
)

# ---------------------------
# Página: Introdução
# ---------------------------
if pagina == "Introdução":
    st.header("Introdução")

    with st.container():
        st.title("Análise de Emoções em Alunos")

        st.markdown("""
        Esta aplicação apresenta um projeto desenvolvido como parte da avaliação da disciplina 
        de **Ferramentas e Soluções em Nuvem** na Pós-graduação em **Mineração de Dados Educacionais** 
        do **Instituto Federal do Espírito Santo - Campus Serra**.

        **Professor:** Maxwell Monteiro  
        **Aluno:** Felippe de Abreu  
        """)

    st.markdown("---")

    with st.expander("🎯 Objetivo do Projeto"):
        st.write("""
        Criar um painel interativo para visualizar e analisar emoções de alunos, buscando padrões
        que possam se relacionar a desempenho acadêmico e risco de evasão.
        """)

    with st.expander("📊 Fonte dos Dados"):
        st.write("""
        - Dataset simulado com emoções (feliz, medo, nervoso, neutro, nojo, triste) + frequência e desempenho;  
        - Bases públicas como **FER2013** e **Student Performance (UCI)** poderão ser integradas futuramente.
        """)

# ---------------------------
# Página: Base de Dados
# ---------------------------
elif pagina == "Base de Dados":
    st.header("Base de Dados")
    st.write("""
    Neste projeto, inicialmente são usadas:
    - Um conjunto simulado de expressões faciais (feliz, medo, nervoso, neutro, nojo, triste);
    - Possível integração futura com **FER2013** e **Student Performance (UCI)**.
    """)

    try:
        df = load_csv("alunos_emocoes_1000.csv")
        st.subheader("Filtros")
        df_filtrado = add_common_filters(df)

        st.markdown("---")
        st.subheader("Visualização da Base de Dados")
        st.dataframe(df_filtrado, use_container_width=True)

        st.markdown("---")
        st.subheader("Estatísticas Descritivas")
        st.dataframe(df_filtrado.describe(include="all"), use_container_width=True)

    except Exception as e:
        st.warning("⚠️ Não foi possível carregar o dataset. Verifique o arquivo 'alunos_emocoes_1000.csv'.")
        st.exception(e)

# ---------------------------
# Página: Visualizações
# ---------------------------
elif pagina == "Visualizações":
    st.header("Visualizações Interativas")

    try:
        df_raw = load_csv("alunos_emocoes_1000.csv")

        # ---- Correções automáticas (sinais/colunas) ----
        df_corr, fixes = _guess_swap_and_sign(df_raw)
        msgs = []
        if fixes["lon_neg"] > 0: msgs.append(f"longitude positiva corrigida: {fixes['lon_neg']}")
        if fixes["lat_neg"] > 0: msgs.append(f"latitude positiva corrigida: {fixes['lat_neg']}")
        if fixes["swapped"]:     msgs.append("colunas lat/lon invertidas foram corrigidas")
        if msgs:
            st.info("Correções aplicadas: " + " · ".join(msgs))

        # ---- Filtros de campo ----
        st.subheader("Filtros")
        df_f = add_common_filters(df_corr)

        st.markdown("---")
        # ---- Opções de mapa ----
        st.subheader("🗺️ Mapa das Emoções por Região (Espírito Santo)")
        with st.expander("Opções do mapa", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                usar_cluster = st.checkbox("Agrupar pontos (cluster)", value=True)
            with c2:
                usar_geojson = st.checkbox("Filtrar usando GeoJSON do ES (opcional)", value=False,
                                           help="Coloque um arquivo 'es_limites.geojson' na pasta do app.")
            with c3:
                marker_size = st.slider("Tamanho do marcador", min_value=5, max_value=18, value=9, step=1)

        # ---- Filtragem geográfica ----
        if usar_geojson and Path("es_limites.geojson").exists():
            df_geo, removed = filter_by_geojson(df_f, "es_limites.geojson")
        else:
            df_geo, removed = filter_es_bounds(df_f)

        if removed > 0:
            st.warning(f"{removed} ponto(s) estavam fora do Espírito Santo e foram removidos.")

        # ---- Plot do mapa (com cluster) ----
        if df_geo.empty:
            st.error("Sem dados para plotar após os filtros.")
        else:
            center = center_from_df(df_geo)

            # Usando go.Scattermapbox para habilitar cluster
            fig_mapa = go.Figure(go.Scattermapbox(
                lat=df_geo["lat"],
                lon=df_geo["lon"],
                mode="markers",
                marker=dict(size=marker_size),
                text=(
                    "Aluno: " + df_geo["id_aluno"].astype(str) +
                    "<br>Região: " + df_geo["regiao"].astype(str) +
                    "<br>Emoção: " + df_geo["dominante_emocao"].astype(str) +
                    "<br>Freq: " + df_geo["frequencia"].astype(str) +
                    "<br>Desemp.: " + df_geo["desempenho"].astype(str)
                ),
                hoverinfo="text",
                cluster=dict(enabled=usar_cluster)
            ))

            fig_mapa.update_layout(
                mapbox=dict(
                    style="open-street-map",  # não requer token
                    center=center,
                    zoom=7
                ),
                margin=dict(l=0, r=0, t=40, b=0),
                title="Distribuição Geográfica das Emoções (ES)"
            )

            st.plotly_chart(fig_mapa, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Gráficos de distribuição
        # ---------------------------
        st.subheader("Distribuição das Emoções")
        contagem_emocoes = df_f["dominante_emocao"].value_counts().reset_index()
        contagem_emocoes.columns = ["Emoção", "Frequência"]

        col3, col4 = st.columns(2)
        with col3:
            fig_bar = px.bar(
                contagem_emocoes, x="Emoção", y="Frequência", color="Emoção",
                text_auto=True, color_discrete_sequence=px.colors.qualitative.Set3,
                title="Contagem por Emoção"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        with col4:
            fig_pie = px.pie(
                contagem_emocoes, names="Emoção", values="Frequência",
                color_discrete_sequence=px.colors.qualitative.Set3, hole=0.3,
                title="Proporção por Emoção"
            )
            fig_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Scatter: Desempenho x Frequência
        # ---------------------------
        st.subheader("Desempenho × Frequência (colorido por emoção)")
        fig_s = px.scatter(
            df_f, x="frequencia", y="desempenho",
            color="dominante_emocao", hover_data=["id_aluno", "regiao"],
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_s.update_traces(marker=dict(size=9, line=dict(width=0)))
        st.plotly_chart(fig_s, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Coordenadas Paralelas
        # ---------------------------
        st.subheader("Relação entre Emoções, Frequência e Desempenho")
        dims = ['score_feliz', 'score_medo', 'score_nervoso', 'score_neutro',
                'score_nojo', 'score_triste', 'frequencia', 'desempenho']
        dims = [d for d in dims if d in df_f.columns]
        fig_parallel = px.parallel_coordinates(
            df_f, color="desempenho", dimensions=dims,
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title="Gráfico de Coordenadas Paralelas"
        )
        st.plotly_chart(fig_parallel, use_container_width=True)

    except Exception as e:
        st.error("Erro ao gerar visualizações.")
        st.exception(e)

# ---------------------------
# Página: Futuras Expansões
# ---------------------------
elif pagina == "Futuras Expansões":
    st.header("Futuras Expansões")
    with st.expander("🔮 Possibilidades Futuras"):
        st.write("""
        - Aplicação de modelos de Machine Learning para identificar emoções automaticamente;
        - Correlação entre emoções, desempenho acadêmico e evasão escolar;
        - Dashboard com filtros por turma, disciplina, período e intervenções;
        - Coleta em tempo real com câmera/webcam integrada.
        """)
