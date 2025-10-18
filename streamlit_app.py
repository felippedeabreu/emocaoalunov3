import streamlit as st
import pandas as pd
import numpy as np

# Try import plotly
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False

st.set_page_config(page_title="Análise de Emoções - Geo", page_icon="🗺️", layout="wide")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Escolha uma seção:", ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"])

# ---------- Utils ----------
@st.cache_data
def load_data(path="alunos_emocoes_1000.csv"):
    return pd.read_csv(path)

# ---------- Introdução ----------
if pagina == "Introdução":
    st.header("Análise de Emoções em Alunos — (Geo & Visualizações)")
    st.write("Painel com foco geográfico para o estado do Espírito Santo. Filtre por região e emoção e veja o mapa e gráficos atualizarem automaticamente.")

# ---------- Base de Dados ----------
elif pagina == "Base de Dados":
    st.header("Base de Dados")
    try:
        df = load_data()
        st.subheader("Preview da Base (1000 registros simulados)")
        st.dataframe(df.head(200), use_container_width=True)

        st.markdown("---")
        st.subheader("Estatísticas Descritivas")
        st.dataframe(df.describe(), use_container_width=True)

        st.markdown("---")
        st.write("Você pode fazer download do dataset completo:")
        st.download_button("📥 Download CSV completo", df.to_csv(index=False).encode('utf-8'), "alunos_emocoes_1000.csv", "text/csv")
    except FileNotFoundError:
        st.error("Arquivo 'alunos_emocoes_1000.csv' não encontrado. Coloque-o na raiz do projeto ou use o CSV que eu gerei.")

# ---------- Visualizações ----------
elif pagina == "Visualizações":
    st.header("Visualizações de Emoções — Mapa e Gráficos")

    try:
        df = load_data()

        # --- Filters ---
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            regiao_filter = st.multiselect("Filtrar por Região", options=['norte','sul','leste','oeste'], default=['norte','sul','leste','oeste'])
        with col2:
            emocao_filter = st.multiselect("Filtrar por Emoção Dominante", options=sorted(df['dominante_emocao'].unique().tolist()), default=sorted(df['dominante_emocao'].unique().tolist()))
        with col3:
            tipo_graf = st.selectbox("Tipo de gráfico para comparação", options=["Barras","Pizza","Scatter","Paralelas"], index=0)

        # Apply filters
        df_f = df[df['regiao'].isin(regiao_filter) & df['dominante_emocao'].isin(emocao_filter)]

        st.markdown(f"**Mostrando {len(df_f)} registros** após filtros.")

        # --- Map ---
        st.subheader("Mapa: Localização dos Alunos no Espírito Santo")
        if PLOTLY_AVAILABLE:
            # Scatter mapbox with OpenStreetMap style (no token required)
            fig_map = px.scatter_mapbox(
                df_f,
                lat="lat",
                lon="lon",
                color="dominante_emocao",
                hover_name="id_aluno",
                hover_data={"regiao":True, "frequencia":True, "desempenho":True},
                size="frequencia",
                size_max=10,
                zoom=6,
                mapbox_style="open-street-map",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, legend_title_text='Emoção Dominante')
            st.plotly_chart(fig_map, use_container_width=True, theme="streamlit")
        else:
            st.warning("Plotly não disponível — instale plotly para ver o mapa interativo.")
            st.map(df_f[['lat','lon']])

        # --- Aggregated bar / pie by emotion ---
        st.markdown("---")
        st.subheader("Distribuição por Emoção (agregada após filtro)")
        agg = df_f['dominante_emocao'].value_counts().reset_index()
        agg.columns = ['Emoção','Frequência']

        if tipo_graf == "Barras":
            fig_bar = px.bar(agg, x='Emoção', y='Frequência', text='Frequência', color='Emoção', color_discrete_sequence=px.colors.qualitative.Set3)
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        elif tipo_graf == "Pizza":
            fig_pie = px.pie(agg, names='Emoção', values='Frequência', color_discrete_sequence=px.colors.qualitative.Set3, title='Distribuição de Emoções')
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        elif tipo_graf == "Scatter":
            st.write("Scatter: Desempenho x Frequência (colorido por emoção)")
            fig_s = px.scatter(df_f, x='frequencia', y='desempenho', color='dominante_emocao', hover_data=['id_aluno','regiao'], trendline='ols', color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_s, use_container_width=True)
        elif tipo_graf == "Paralelas":
            st.write("Coordenadas paralelas: scores das emoções + desempenho")
            pcs_cols = [c for c in df_f.columns if c.startswith('score_')] + ['desempenho']
            # Normalize scores/desempenho for plotting clarity
            df_pc = df_f[pcs_cols].copy()
            # plotly parallel coordinates needs numeric columns
            fig_pc = px.parallel_coordinates(df_pc, color=df_f['desempenho'], labels={c:c for c in pcs_cols}, color_continuous_scale=px.colors.sequential.Viridis)
            st.plotly_chart(fig_pc, use_container_width=True)

        # --- Comparison: desempenho médio por emoção ---
        st.markdown("---")
        st.subheader("Comparativo de Desempenho por Emoção")
        perf = df_f.groupby('dominante_emocao')['desempenho'].agg(['mean','count']).reset_index().sort_values('mean', ascending=False)
        perf.columns = ['Emoção','Desempenho Médio','Contagem']
        fig_perf = px.bar(perf, x='Emoção', y='Desempenho Médio', text='Desempenho Médio', color='Emoção', color_discrete_sequence=px.colors.qualitative.Set3)
        fig_perf.update_layout(yaxis_title='Desempenho Médio (%)', showlegend=False)
        st.plotly_chart(fig_perf, use_container_width=True)

        # --- Scatter: desempenho vs frequência com legenda ---
        st.markdown("---")
        st.subheader("Desempenho vs Frequência (cada ponto = aluno)")
        fig_sf = px.scatter(df_f, x='frequencia', y='desempenho', color='dominante_emocao', hover_data=['id_aluno','regiao'], color_discrete_sequence=px.colors.qualitative.Set2)
        fig_sf.update_layout(xaxis_title='Frequência (%)', yaxis_title='Desempenho (%)', legend_title='Emoção')
        st.plotly_chart(fig_sf, use_container_width=True)

        # --- Download filtered CSV ---
        st.markdown("---")
        st.download_button("📥 Download CSV filtrado", df_f.to_csv(index=False).encode('utf-8'), "alunos_emocoes_filtrado.csv", "text/csv")

    except FileNotFoundError:
        st.error("Arquivo 'alunos_emocoes_1000.csv' não encontrado. Coloque-o na raiz do projeto ou use o CSV que eu gerei.")
    except Exception as e:
        st.error("Erro ao gerar visualizações.")
        st.exception(e)

# ---------- Futuras Expansões ----------
elif pagina == "Futuras Expansões":
    st.header("Futuras Expansões")
    st.write("""
    - Ajustar o GeoJSON para desenhar polígonos reais das regiões (norte/sul/leste/oeste) do ES;
    - Implementar agregação por município e heatmap por densidade;
    - Integrar modelagem para predizer risco de evasão a partir de emoções e métricas;
    - Permitir upload de CSV pelo usuário para análises dinâmicas.
    """)
