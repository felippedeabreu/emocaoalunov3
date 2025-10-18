import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---------------------------
# Configuração da página (uma única vez)
# ---------------------------
st.set_page_config(
    page_title="Análise de Emoções em Alunos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------
# Loader com cache e fallback para o CSV original
# ---------------------------
@st.cache_data(show_spinner=False)
def carregar_dados():
    for path in ["alunos_emocoes_1000_corrigido.csv", "alunos_emocoes_1000.csv"]:
        try:
            df_ = pd.read_csv(path)
            return df_, path
        except Exception:
            continue
    return None, None

# ---------------------------
# Menu lateral (com key)
# ---------------------------
st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Escolha uma seção:",
    ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"],
    key="nav"
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
        O objetivo é criar um painel interativo para visualização e análise das emoções dos alunos, 
        buscando identificar padrões emocionais que possam estar relacionados ao desempenho acadêmico 
        e ao risco de evasão escolar.
        """)

    with st.expander("📊 Fonte dos Dados"):
        st.write("""
        Para este protótipo inicial, estão sendo utilizados:
        - **Dataset simulado** contendo expressões faciais (feliz, medo, nervoso, neutro, nojo e triste), 
          junto com indicadores de frequência e desempenho escolar;
        - Bases públicas como **FER2013** (reconhecimento de emoções) e **Student Performance Dataset** (UCI), 
          que poderão ser integradas em versões futuras.
        """)

# ---------------------------
# Página: Base de Dados
# ---------------------------
elif pagina == "Base de Dados":
    st.header("Base de Dados")
    st.write("""
    Neste projeto, inicialmente serão utilizadas duas abordagens:
    - Um conjunto de dados simulados de expressões faciais (feliz, medo, nervoso, neutro, nojo e triste);
    - Bases públicas como **FER2013** (reconhecimento de emoções) e **Student Performance Dataset** (UCI).
    """)

    df, origem = carregar_dados()
    if df is None:
        st.warning("⚠️ Não foi possível carregar nenhum dataset. Verifique se o CSV está na pasta do app.")
    else:
        st.caption(f"Fonte atual de dados: **{origem}**")

        st.subheader("Filtros")
        col1, col2 = st.columns(2)

        with col1:
            emocao_selecionada = st.selectbox(
                "Selecione uma emoção:",
                ["Todas"] + sorted(df["dominante_emocao"].dropna().unique().tolist()),
                key="emocao_bd"
            )
        with col2:
            regiao_selecionada = st.selectbox(
                "Selecione uma região:",
                ["Todas"] + sorted(df["regiao"].dropna().unique().tolist()),
                key="regiao_bd"
            )

        # Aplicação dos filtros básicos
        df_filtrado = df.copy()
        if emocao_selecionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["dominante_emocao"] == emocao_selecionada]
        if regiao_selecionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["regiao"] == regiao_selecionada]

        # -------- Filtros avançados --------
        with st.expander("Filtros avançados", expanded=False):
            # Faixa de desempenho
            if "desempenho" in df_filtrado.columns and pd.api.types.is_numeric_dtype(df_filtrado["desempenho"]):
                des_min, des_max = float(df["desempenho"].min()), float(df["desempenho"].max())
                f_des = st.slider(
                    "Faixa de desempenho",
                    des_min, des_max,
                    (des_min, des_max), step=0.1, key="desempenho_bd_range"
                )
            else:
                f_des = (None, None)

            # Faixa de frequência
            if "frequencia" in df_filtrado.columns and pd.api.types.is_numeric_dtype(df_filtrado["frequencia"]):
                fr_min, fr_max = float(df["frequencia"].min()), float(df["frequencia"].max())
                f_frq = st.slider(
                    "Faixa de frequência (%)",
                    fr_min, fr_max,
                    (fr_min, fr_max), step=1.0, key="freq_bd_range"
                )
            else:
                f_frq = (None, None)

        # Aplica filtros avançados se válidos
        if all(v is not None for v in f_des):
            df_filtrado = df_filtrado[df_filtrado["desempenho"].between(f_des[0], f_des[1])]
        if all(v is not None for v in f_frq):
            df_filtrado = df_filtrado[df_filtrado["frequencia"].between(f_frq[0], f_frq[1])]

        st.markdown("---")
        st.subheader("Visualização da Base de Dados")
        st.dataframe(df_filtrado, use_container_width=True)

        st.markdown("---")
        st.subheader("Estatísticas Descritivas")
        try:
            st.dataframe(df_filtrado.describe(), use_container_width=True)
        except Exception:
            st.info("Não foi possível gerar estatísticas descritivas (verifique se há colunas numéricas).")

# ---------------------------
# Página: Visualizações
# ---------------------------
elif pagina == "Visualizações":
    st.header("Visualizações Interativas")

    df, origem = carregar_dados()
    if df is None:
        st.error("Erro ao carregar os dados. Verifique os arquivos CSV.")
    else:
        st.caption(f"Fonte atual de dados: **{origem}**")

        # Filtros (com keys únicas)
        col1, col2 = st.columns(2)
        with col1:
            emocao_filtro = st.selectbox(
                "Filtrar por emoção:",
                ["Todas"] + sorted(df["dominante_emocao"].dropna().unique()),
                key="emocao_vis"
            )
        with col2:
            regiao_filtro = st.selectbox(
                "Filtrar por região:",
                ["Todas"] + sorted(df["regiao"].dropna().unique()),
                key="regiao_vis"
            )

        # Slider de altura do mapa na sidebar
        map_height = st.sidebar.slider(
            "Altura do mapa (px)", 600, 1600, 800, step=50, key="map_h"
        )

        # Aplica filtros
        df_f = df.copy()
        if emocao_filtro != "Todas":
            df_f = df_f[df_f["dominante_emocao"] == emocao_filtro]
        if regiao_filtro != "Todas":
            df_f = df_f[df_f["regiao"] == regiao_filtro]

        if df_f.empty:
            st.info("Nenhum dado após os filtros selecionados.")
            st.stop()

        # ---------------------------
        # Mapa
        # ---------------------------
        st.markdown("### 🗺️ Mapa das Emoções por Região (Espírito Santo)")
        hover_cols = [c for c in ["id_aluno", "regiao", "frequencia", "desempenho"] if c in df_f.columns]
        fig_mapa = px.scatter_mapbox(
            df_f,
            lat="lat",
            lon="lon",
            color="dominante_emocao",
            hover_data=hover_cols,
            zoom=7,
            height=map_height,
            mapbox_style="carto-positron",
            title="Distribuição Geográfica das Emoções",
            labels={"dominante_emocao": "Emoção dominante"}
        )
        # Legenda e margens
        fig_mapa.update_layout(
            legend_title_text="Emoção dominante",
            margin=dict(l=0, r=0, t=40, b=0)
        )
        # Centraliza conforme o filtro
        if {"lat", "lon"}.issubset(df_f.columns):
            fig_mapa.update_layout(
                mapbox=dict(center=dict(
                    lat=float(df_f["lat"].mean()),
                    lon=float(df_f["lon"].mean())
                ), zoom=7)
            )
        st.plotly_chart(fig_mapa, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Distribuição das Emoções
        # ---------------------------
        st.subheader("Distribuição das Emoções")
        contagem_emocoes = df_f["dominante_emocao"].value_counts().reset_index()
        contagem_emocoes.columns = ["Emoção", "Frequência"]
        contagem_emocoes = contagem_emocoes.sort_values("Frequência", ascending=False)

        col3, col4 = st.columns(2)
        with col3:
            fig_bar = px.bar(
                contagem_emocoes, x="Emoção", y="Frequência",
                color="Emoção", text_auto=True,
                color_discrete_sequence=px.colors.qualitative.Set3,
                labels={"Emoção": "Emoção", "Frequência": "Quantidade"}
            )
            fig_bar.update_layout(legend_title_text="Emoção dominante")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col4:
            fig_pie = px.pie(
                contagem_emocoes, names="Emoção", values="Frequência",
                hole=0.35, title="Distribuição de Emoções",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textinfo="percent+label", pull=0.02)
            fig_pie.update_layout(legend_title_text="Emoção dominante")
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Scatter: Desempenho x Frequência
        # ---------------------------
        st.subheader("Scatter: Desempenho x Frequência (colorido por emoção)")
        if {"frequencia", "desempenho"}.issubset(df_f.columns):
            fig_s = px.scatter(
                df_f, x='frequencia', y='desempenho',
                color='dominante_emocao' if 'dominante_emocao' in df_f.columns else None,
                hover_data=[c for c in ['id_aluno', 'regiao'] if c in df_f.columns],
                color_discrete_sequence=px.colors.qualitative.Set2,
                labels={"frequencia": "Frequência (%)", "desempenho": "Desempenho"}
            )
            fig_s.update_layout(legend_title_text="Emoção dominante")
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("Não há colunas suficientes para o gráfico de dispersão (requer 'frequencia' e 'desempenho').")

        st.markdown("---")
        # ---------------------------
        # Gráfico de Coordenadas Paralelas
        # ---------------------------
        st.subheader("Gráfico de Coordenadas Paralelas")
        alvo_dims = [
            'score_feliz', 'score_medo', 'score_nervoso',
            'score_neutro', 'score_nojo', 'score_triste',
            'frequencia', 'desempenho'
        ]
        dims_ok = [c for c in alvo_dims if c in df_f.columns and pd.api.types.is_numeric_dtype(df_f[c])]
        if len(dims_ok) >= 2:
            fig_parallel = px.parallel_coordinates(
                df_f,
                color="desempenho" if "desempenho" in df_f.columns else None,
                dimensions=dims_ok,
                color_continuous_scale=px.colors.diverging.RdYlGn,
                title="Relação entre Emoções, Frequência e Desempenho",
                labels={c: c.replace("_", " ").title() for c in dims_ok}
            )
            st.plotly_chart(fig_parallel, use_container_width=True)
        else:
            st.info("Colunas insuficientes para o gráfico de coordenadas paralelas.")

        st.markdown("---")
        # ---------------------------
        # Comparação direta: Desempenho por Emoção
        # ---------------------------
        st.subheader("Desempenho por Emoção (comparação)")
        if {"dominante_emocao", "desempenho"}.issubset(df_f.columns):
            agg = (
                df_f.groupby("dominante_emocao", dropna=False)
                    .agg(media_desempenho=("desempenho", "mean"),
                         media_frequencia=("frequencia", "mean") if "frequencia" in df_f.columns else ("desempenho", "size"),
                         n=("id_aluno", "count") if "id_aluno" in df_f.columns else ("dominante_emocao", "size"))
                    .reset_index()
            )
            if "media_frequencia" not in agg.columns:
                agg["media_frequencia"] = pd.NA
            agg = agg.sort_values("media_desempenho", ascending=False)

            colA, colB = st.columns(2)

            with colA:
                fig_perf_bar = px.bar(
                    agg, x="dominante_emocao", y="media_desempenho",
                    text="media_desempenho",
                    title="Média de Desempenho por Emoção",
                    labels={"dominante_emocao": "Emoção", "media_desempenho": "Média de desempenho"},
                    color="dominante_emocao", color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_perf_bar.update_traces(texttemplate="%{text:.2f}")
                fig_perf_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_perf_bar, use_container_width=True)

            with colB:
                if agg["media_frequencia"].notna().any():
                    fig_freq_bar = px.bar(
                        agg, x="dominante_emocao", y="media_frequencia",
                        text="media_frequencia",
                        title="Média de Frequência por Emoção",
                        labels={"dominante_emocao": "Emoção", "media_frequencia": "Média de frequência (%)"},
                        color="dominante_emocao", color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_freq_bar.update_traces(texttemplate="%{text:.1f}")
                    fig_freq_bar.update_layout(showlegend=False)
                    st.plotly_chart(fig_freq_bar, use_container_width=True)
                else:
                    st.info("Coluna 'frequencia' não disponível para média por emoção.")

            # ---------------------------
            # Boxplot de distribuição (ordenado + escala)
            # ---------------------------
            st.markdown("### Distribuição do Desempenho por Emoção")
            fig_box = px.box(
                df_f, x="dominante_emocao", y="desempenho", points="all",
                labels={"dominante_emocao": "Emoção", "desempenho": "Desempenho"},
                title="Boxplot de Desempenho por Emoção",
                color="dominante_emocao", color_discrete_sequence=px.colors.qualitative.Set1
            )
            fig_box.update_layout(showlegend=False)

            # Detecta escala automaticamente
            if "desempenho" in df_f.columns and not df_f["desempenho"].empty:
                max_des = float(df_f["desempenho"].max())
                escala = "0–10" if max_des <= 10 else "0–100"
            else:
                escala = "0–100"
            fig_box.update_layout(yaxis_title=f"Desempenho ({escala})")

            # Ordena emoções pela mediana (decrescente)
            order = (
                df_f.groupby("dominante_emocao")["desempenho"]
                    .median()
                    .sort_values(ascending=False)
                    .index
            )
            fig_box.update_xaxes(categoryorder="array", categoryarray=order)

            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Dados insuficientes para comparar desempenho por emoção.")

        st.markdown("---")
        # ---------------------------
        # Correlação: Desempenho × Frequência
        # ---------------------------
        st.subheader("Correlação: Desempenho × Frequência")
        if {"desempenho", "frequencia"}.issubset(df_f.columns):
            # Correlação geral (Pearson)
            if df_f[["desempenho", "frequencia"]].dropna().shape[0] >= 2:
                corr_geral = df_f[["desempenho", "frequencia"]].corr(method="pearson").iloc[0, 1]
                st.metric("Correlação geral (Pearson)", f"{corr_geral:.2f}")
            else:
                st.metric("Correlação geral (Pearson)", "N/A")

            # Correlação por emoção
            corr_por_emo = (
                df_f.groupby("dominante_emocao")
                    .apply(lambda g: g["desempenho"].corr(g["frequencia"]))
                    .reset_index(name="correlacao_pearson")
                    .sort_values("correlacao_pearson", ascending=False)
            )
            st.dataframe(corr_por_emo, use_container_width=True)

            # Heatmap de correlação entre numéricas
            num_cols = df_f.select_dtypes(include="number").columns
            if len(num_cols) >= 2:
                fig_heat = px.imshow(
                    df_f[num_cols].corr().round(2),
                    text_auto=True,
                    color_continuous_scale="RdBu",
                    origin="lower",
                    title="Matriz de correlação (colunas numéricas)"
                )
                st.plotly_chart(fig_heat, use_container_width=True)

            # Dispersão com facetas por emoção
            st.markdown("### Dispersão por emoção (Frequência × Desempenho)")
            fig_facets = px.scatter(
                df_f,
                x="frequencia", y="desempenho",
                color="dominante_emocao",
                facet_col="dominante_emocao", facet_col_wrap=3,
                opacity=0.7,
                hover_data=[c for c in ["id_aluno", "regiao"] if c in df_f.columns],
                labels={"frequencia": "Frequência (%)", "desempenho": f"Desempenho ({escala})"}
            )
            fig_facets.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_facets, use_container_width=True)
        else:
            st.info("Para calcular correlação, preciso das colunas 'desempenho' e 'frequencia'.")

# ---------------------------
# Página: Futuras Expansões
# ---------------------------
elif pagina == "Futuras Expansões":
    st.header("Futuras Expansões")
    with st.expander("🔮 Possibilidades Futuras"):
        st.write("""
        - Aplicação de modelos de Machine Learning para identificar emoções automaticamente;
        - Correlação entre emoções, desempenho acadêmico e evasão escolar;
        - Dashboard interativo com filtros por turma, disciplina e período;
        - Coleta em tempo real usando câmera/webcam integrada.
        """)
