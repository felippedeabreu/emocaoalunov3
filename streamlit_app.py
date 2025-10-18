# app.py
# -----------------------------------------------------------
# Painel: Análise de Emoções em Alunos (Espírito Santo)
# - Usa geojs-32-mun.json (municípios do ES) para filtrar pontos
# - Contorno/preenchimento do ES no mapa (Mapbox layer)
# - Cluster ON/OFF e pontos coloridos por emoção
# - Correções automáticas de lat/lon (sinal e inversão de colunas)
# -----------------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

st.set_page_config(page_title="Análise de Emoções em Alunos", page_icon="📊", layout="wide")

# ---------------------------
# Arquivo GeoJSON e limites/centro do ES (fallback)
# ---------------------------
GEOJSON_ES = "geojs-32-mun.json"  # use o arquivo enviado
ES_CENTER = {"lat": -19.5, "lon": -40.5}
ES_BOUNDS = {"lat_min": -21.4, "lat_max": -18.0, "lon_min": -41.9, "lon_max": -39.0}

# ---------------------------
# Utilidades
# ---------------------------
@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normaliza vírgula decimal e strings estranhas
    for col in ["lat", "lon"]:
        if col in df.columns and df[col].dtype == "object":
            df[col] = (
                df[col].astype(str)
                .str.replace(",", ".", regex=False)
                .str.extract(r"(-?\d+(?:\.\d+)?)")[0]
                .astype(float)
            )
    return df

@st.cache_data(show_spinner=False)
def load_geojson(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _guess_swap_and_sign(df: pd.DataFrame) -> (pd.DataFrame, dict):
    """
    Corrige problemas comuns de geocodificação:
    - longitude positiva (torna negativa)
    - latitude positiva (torna negativa)
    - colunas lat/lon invertidas
    """
    fixes = {"lon_neg": 0, "lat_neg": 0, "swapped": False}
    d = df.copy()

    if (d["lon"] > 0).mean() > 0.6:
        d["lon"] = -d["lon"]
        fixes["lon_neg"] = int((df["lon"] > 0).sum())

    if (d["lat"] > 0).mean() > 0.6:
        d["lat"] = -d["lat"]
        fixes["lat_neg"] = int((df["lat"] > 0).sum())

    # ES: lon típica ~ -40; lat ~ -19  → se inverteram, detecta
    if d["lon"].abs().mean() < 30 and d["lat"].abs().mean() > 30:
        d[["lat", "lon"]] = d[["lon", "lat"]]
        fixes["swapped"] = True

    return d, fixes

def filter_es_bounds(df: pd.DataFrame) -> (pd.DataFrame, int):
    mask = (
        df["lat"].between(ES_BOUNDS["lat_min"], ES_BOUNDS["lat_max"])
        & df["lon"].between(ES_BOUNDS["lon_min"], ES_BOUNDS["lon_max"])
    )
    return df.loc[mask].copy(), int((~mask).sum())

def filter_by_geojson(df: pd.DataFrame, geojson_path: str) -> (pd.DataFrame, int, dict):
    """
    Filtra pontos dentro do polígono do ES utilizando Shapely (se disponível).
    Retorna df_filtrado, removidos, e o objeto GeoJSON (para desenhar no mapa).
    """
    gj = load_geojson(geojson_path)
    try:
        from shapely.geometry import shape, Point
        from shapely.ops import unary_union
        from shapely.prepared import prep

        polys = [shape(feat["geometry"]) for feat in gj["features"]]
        es_poly = unary_union(polys)
        es_prep = prep(es_poly)

        # inclui pontos "na borda" (touches) como válidos
        mask = []
        for x, y in zip(df["lon"].to_numpy(), df["lat"].to_numpy()):
            p = Point(x, y)
            mask.append(es_prep.contains(p) or es_poly.touches(p))
        mask = np.array(mask, dtype=bool)

        removed = int((~mask).sum())
        return df.loc[mask].copy(), removed, gj
    except Exception:
        # Fallback para bounding box
        dfb, removed = filter_es_bounds(df)
        return dfb, removed, gj  # ainda retornamos o GeoJSON para desenhar contorno

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
# Menu
# ---------------------------
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Escolha uma seção:", ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"])

# ---------------------------
# Introdução
# ---------------------------
if pagina == "Introdução":
    st.header("Introdução")
    st.title("Análise de Emoções em Alunos")
    st.markdown("""
    Projeto da disciplina **Ferramentas e Soluções em Nuvem** (Pós **Mineração de Dados Educacionais** — IFES/Serra).  
    **Professor:** Maxwell Monteiro — **Aluno:** Felippe de Abreu
    """)
    st.markdown("---")
    with st.expander("🎯 Objetivo do Projeto"):
        st.write("Criar um painel interativo para visualizar e analisar emoções e possíveis relações com desempenho e evasão.")
    with st.expander("📊 Fontes de Dados"):
        st.write("- Dataset simulado (emoções, frequência, desempenho). Integrações futuras: **FER2013**, **UCI Student Performance**.")

# ---------------------------
# Base de Dados
# ---------------------------
elif pagina == "Base de Dados":
    st.header("Base de Dados")
    try:
        df = load_csv("alunos_emocoes_1000.csv")
        st.subheader("Filtros")
        df_filtrado = add_common_filters(df)
        st.markdown("---")
        st.subheader("Visualização")
        st.dataframe(df_filtrado, use_container_width=True)
        st.markdown("---")
        st.subheader("Estatísticas Descritivas")
        st.dataframe(df_filtrado.describe(include="all"), use_container_width=True)
    except Exception as e:
        st.warning("⚠️ Não foi possível carregar 'alunos_emocoes_1000.csv'.")
        st.exception(e)

# ---------------------------
# Visualizações
# ---------------------------
elif pagina == "Visualizações":
    st.header("Visualizações Interativas")
    try:
        df_raw = load_csv("alunos_emocoes_1000.csv")

        # Correções de lat/lon
        df_corr, fixes = _guess_swap_and_sign(df_raw)
        msgs = []
        if fixes["lon_neg"] > 0: msgs.append(f"longitude positiva corrigida: {fixes['lon_neg']}")
        if fixes["lat_neg"] > 0: msgs.append(f"latitude positiva corrigida: {fixes['lat_neg']}")
        if fixes["swapped"]:     msgs.append("colunas lat/lon invertidas foram corrigidas")
        if msgs:
            st.info("Correções: " + " · ".join(msgs))

        st.subheader("Filtros")
        df_f = add_common_filters(df_corr)
        st.markdown("---")

        # ---------------------------
        # Mapa
        # ---------------------------
        st.subheader("🗺️ Mapa das Emoções por Região (Espírito Santo)")

        c1, c2, c3 = st.columns(3)
        with c1:
            modo_mapa = st.radio("Visualização:", ["Clusters", "Pontos por emoção"], horizontal=True)
        with c2:
            marker_size = st.slider("Tamanho do marcador", 5, 18, 9, 1)
        with c3:
            preencher = st.checkbox("Preencher o polígono do ES", value=False, help="Desenha um fill suave do estado.")

        if Path(GEOJSON_ES).exists():
            df_geo, removidos, es_geojson = filter_by_geojson(df_f, GEOJSON_ES)
        else:
            df_geo, removidos = filter_es_bounds(df_f)
            es_geojson = None

        if removidos > 0:
            st.warning(f"{removidos} ponto(s) fora do Espírito Santo foram removidos.")

        if df_geo.empty:
            st.error("Sem dados para plotar após os filtros.")
        else:
            center = center_from_df(df_geo)

            if modo_mapa == "Clusters":
                fig_mapa = go.Figure(go.Scattermapbox(
                    lat=df_geo["lat"], lon=df_geo["lon"],
                    mode="markers",
                    marker=dict(size=marker_size, color="#4c5563"),
                    text=("Aluno: " + df_geo["id_aluno"].astype(str)
                          + "<br>Região: " + df_geo["regiao"].astype(str)
                          + "<br>Emoção: " + df_geo["dominante_emocao"].astype(str)
                          + "<br>Freq: " + df_geo["frequencia"].astype(str)
                          + "<br>Desemp.: " + df_geo["desempenho"].astype(str)),
                    hoverinfo="text",
                    cluster=dict(enabled=True)
                ))
            else:
                fig_mapa = go.Figure()
                for emocao, dfg in df_geo.groupby("dominante_emocao"):
                    fig_mapa.add_trace(go.Scattermapbox(
                        lat=dfg["lat"], lon=dfg["lon"],
                        name=str(emocao),
                        mode="markers",
                        marker=dict(size=marker_size),
                        text=("Aluno: " + dfg["id_aluno"].astype(str)
                              + "<br>Região: " + dfg["regiao"].astype(str)
                              + "<br>Emoção: " + dfg["dominante_emocao"].astype(str)
                              + "<br>Freq: " + dfg["frequencia"].astype(str)
                              + "<br>Desemp.: " + dfg["desempenho"].astype(str)),
                        hoverinfo="text"
                    ))

            # Base do mapa
            fig_mapa.update_layout(
                mapbox=dict(style="open-street-map", center=center, zoom=7),
                margin=dict(l=0, r=0, t=40, b=0),
                title="Distribuição Geográfica das Emoções (ES)"
            )

            # Desenhar contorno (e, opcionalmente, preenchimento) do ES
            layers = []
            if es_geojson:
                if preencher:
                    layers.append({
                        "source": es_geojson, "type": "fill",
                        "color": "#6B5FB5", "opacity": 0.05
                    })
                layers.append({
                    "source": es_geojson, "type": "line",
                    "color": "#6B5FB5", "line": {"width": 2}
                })
            if layers:
                fig_mapa.update_layout(mapbox_layers=layers)

            st.plotly_chart(fig_mapa, use_container_width=True)

        st.markdown("---")
        # Distribuição das emoções
        st.subheader("Distribuição das Emoções")
        cont = df_f["dominante_emocao"].value_counts().reset_index()
        cont.columns = ["Emoção", "Frequência"]

        col3, col4 = st.columns(2)
        with col3:
            fig_bar = px.bar(cont, x="Emoção", y="Frequência", color="Emoção",
                             text_auto=True, color_discrete_sequence=px.colors.qualitative.Set3,
                             title="Contagem por Emoção")
            st.plotly_chart(fig_bar, use_container_width=True)
        with col4:
            fig_pie = px.pie(cont, names="Emoção", values="Frequência",
                             color_discrete_sequence=px.colors.qualitative.Set3, hole=0.3,
                             title="Proporção por Emoção")
            fig_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        # Scatter desempenho x frequência
        st.subheader("Desempenho × Frequência (colorido por emoção)")
        fig_s = px.scatter(df_f, x="frequencia", y="desempenho",
                           color="dominante_emocao", hover_data=["id_aluno", "regiao"],
                           color_discrete_sequence=px.colors.qualitative.Set2)
        fig_s.update_traces(marker=dict(size=9, line=dict(width=0)))
        st.plotly_chart(fig_s, use_container_width=True)

        st.markdown("---")
        # Coordenadas paralelas
        st.subheader("Relação entre Emoções, Frequência e Desempenho")
        dims = ['score_feliz', 'score_medo', 'score_nervoso', 'score_neutro',
                'score_nojo', 'score_triste', 'frequencia', 'desempenho']
        dims = [d for d in dims if d in df_f.columns]
        if dims:
            fig_parallel = px.parallel_coordinates(
                df_f, color="desempenho", dimensions=dims,
                color_continuous_scale=px.colors.diverging.RdYlGn,
                title="Gráfico de Coordenadas Paralelas"
            )
            st.plotly_chart(fig_parallel, use_container_width=True)
        else:
            st.info("Colunas para coordenadas paralelas não encontradas no dataset.")

    except Exception as e:
        st.error("Erro ao gerar visualizações.")
        st.exception(e)

# ---------------------------
# Futuras Expansões
# ---------------------------
elif pagina == "Futuras Expansões":
    st.header("Futuras Expansões")
    with st.expander("🔮 Possibilidades"):
        st.write("""
        - Modelos de ML para identificar emoções automaticamente;
        - Correlações entre emoções, desempenho e evasão;
        - Filtros por turma/disciplina/período; coleta em tempo real via webcam.
        """)
