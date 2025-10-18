import streamlit as st
import pandas as pd
import numpy as np

# Tentativa de importar plotly e statsmodels
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False

try:
    import statsmodels.api as sm  # usado pelo plotly trendline='ols' (se disponível)
    STATSMODELS_AVAILABLE = True
except Exception:
    STATSMODELS_AVAILABLE = False

st.set_page_config(page_title="Análise de Emoções - Geo (corrigido)", page_icon="🗺️", layout="wide")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Escolha uma seção:", ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"])

@st.cache_data
def load_data(path="alunos_emocoes_1000.csv"):
    return pd.read_csv(path)

if pagina == "Introdução":
    st.header("Análise de Emoções em Alunos — (Geo & Visualizações)")
    st.write("Versão corrigida: fallback de trendline sem statsmodels; mapa centraliza de acordo com dados.")

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
        st.download_button("📥 Download CSV completo", df.to_csv(index=False).encode('utf-8'), "alunos_emocoes_1000.csv", "text/csv")
    except FileNotFoundError:
        st.error("Arquivo 'alunos_emocoes_1000.csv' não encontrado. Coloque-o na raiz do projeto.")

elif pagina == "Visualizações":
    st.header("Visualizações de Emoções — Mapa e Gráficos (corrigido)")

    try:
        df = load_data()

        # ---- filtros ----
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            regiao_filter = st.multiselect("Filtrar por Região", options=['norte','sul','leste','oeste'], default=['norte','sul','leste','oeste'])
        with col2:
            emocao_filter = st.multiselect("Filtrar por Emoção Dominante", options=sorted(df['dominante_emocao'].unique().tolist()), default=sorted(df['dominante_emocao'].unique().tolist()))
        with col3:
            tipo_graf = st.selectbox("Tipo de gráfico para comparação", options=["Barras","Pizza","Scatter","Paralelas"], index=0)

        df_f = df[df['regiao'].isin(regiao_filter) & df['dominante_emocao'].isin(emocao_filter)]
        st.markdown(f"**Mostrando {len(df_f)} registros** após filtros.")

        # ---- MAPA: centraliza no conjunto filtrado ----
        st.subheader("Mapa: Localização dos Alunos no Espírito Santo")
        if len(df_f) == 0:
            st.warning("Nenhum registro após filtros — ajuste filtros para ver o mapa.")
        else:
            if PLOTLY_AVAILABLE:
                # centraliza no centro dos pontos filtrados para garantir cobertura sul/norte
                center_lat = float(df_f['lat'].mean())
                center_lon = float(df_f['lon'].mean())
                # zoom ajustável — se muitos pontos, zoom menor
                zoom = 6.0
                fig_map = px.scatter_mapbox(
                    df_f,
                    lat="lat",
                    lon="lon",
                    color="dominante_emocao",
                    hover_name="id_aluno",
                    hover_data={"regiao":True, "frequencia":True, "desempenho":True},
                    size="frequencia",
                    size_max=12,
                    opacity=0.75,
                    zoom=zoom,
                    mapbox_style="open-street-map",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    center={"lat": center_lat, "lon": center_lon}
                )
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, legend_title_text='Emoção Dominante')
                st.plotly_chart(fig_map, use_container_width=True, theme="streamlit")
            else:
                st.warning("Plotly não disponível — instale plotly (`pip install plotly`) para mapa interativo.")
                st.map(df_f[['lat','lon']])

        # ---- Distribuição por emoção ----
        st.markdown("---")
        st.subheader("Distribuição por Emoção (após filtro)")
        agg = df_f['dominante_emocao'].value_counts().reset_index()
        agg.columns = ['Emoção','Frequência']

        if tipo_graf == "Barras":
            if PLOTLY_AVAILABLE:
                fig_bar = px.bar(agg, x='Emoção', y='Frequência', text='Frequência', color='Emoção', color_discrete_sequence=px.colors.qualitative.Set3)
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.bar_chart(agg.set_index('Emoção'))
        elif tipo_graf == "Pizza":
            if PLOTLY_AVAILABLE:
                fig_pie = px.pie(agg, names='Emoção', values='Frequência', color_discrete_sequence=px.colors.qualitative.Set3, title='Distribuição de Emoções')
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.table(agg)
        elif tipo_graf == "Scatter":
            st.write("Scatter: Desempenho x Frequência (colorido por emoção)")
            if len(df_f) == 0:
                st.info("Sem dados para scatter.")
            else:
                if PLOTLY_AVAILABLE:
                    # Se statsmodels disponível, usamos trendline do plotly; senão fazemos fallback manual
                    if STATSMODELS_AVAILABLE:
                        fig_s = px.scatter(
                            df_f,
                            x='frequencia',
                            y='desempenho',
                            color='dominante_emocao',
                            hover_data=['id_aluno','regiao'],
                            trendline='ols',
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        st.plotly_chart(fig_s, use_container_width=True)
                    else:
                        # fallback: scatter + linhas de tendência por emoção com numpy.polyfit (não precisa de statsmodels)
                        fig = px.scatter(df_f, x='frequencia', y='desempenho', color='dominante_emocao', hover_data=['id_aluno','regiao'], color_discrete_sequence=px.colors.qualitative.Set2)
                        # calcular e adicionar linhas de regressão por grupo
                        unique_em = df_f['dominante_emocao'].unique()
                        x_min, x_max = df_f['frequencia'].min(), df_f['frequencia'].max()
                        xs = np.linspace(x_min, x_max, 100)
                        for em in unique_em:
                            grp = df_f[df_f['dominante_emocao'] == em]
                            if len(grp) >= 2:
                                # ajuste linear simples
                                coef = np.polyfit(grp['frequencia'], grp['desempenho'], 1)
                                ys = np.polyval(coef, xs)
                                fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', name=f"Trend: {em}", showlegend=True))
                        fig.update_layout(xaxis_title='Frequência (%)', yaxis_title='Desempenho (%)', legend_title='Emoção')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Plotly não disponível — mostrando tabela resumo em vez do scatter.")
                    st.dataframe(df_f[['frequencia','desempenho','dominante_emocao']].head(200))

        elif tipo_graf == "Paralelas":
            st.write("Coordenadas paralelas: scores das emoções + desempenho")
            pcs_cols = [c for c in df_f.columns if c.startswith('score_')] + ['desempenho']
            if len(df_f) == 0:
                st.info("Sem dados para coordenadas paralelas.")
            elif PLOTLY_AVAILABLE:
                df_pc = df_f[pcs_cols].copy()
                fig_pc = px.parallel_coordinates(df_pc, color=df_f['desempenho'], labels={c:c for c in pcs_cols}, color_continuous_scale=px.colors.sequential.Viridis)
                st.plotly_chart(fig_pc, use_container_width=True)
            else:
                st.warning("Plotly não disponível — não é possível mostrar paralelas.")

        # ---- Comparativo desempenho por emoção ----
        st.markdown("---")
        st.subheader("Comparativo de Desempenho por Emoção")
        if len(df_f) == 0:
            st.info("Sem dados para comparar desempenho.")
        else:
            perf = df_f.groupby('dominante_emocao')['desempenho'].agg(['mean','count']).reset_index().sort_values('mean', ascending=False)
            perf.columns = ['Emoção','Desempenho Médio','Contagem']
            if PLOTLY_AVAILABLE:
                fig_perf = px.bar(perf, x='Emoção', y='Desempenho Médio', text='Desempenho Médio', color='Emoção', color_discrete_sequence=px.colors.qualitative.Set3)
                fig_perf.update_layout(yaxis_title='Desempenho Médio (%)', showlegend=False)
                st.plotly_chart(fig_perf, use_container_width=True)
            else:
                st.dataframe(perf)

        # ---- Scatter simples desempenho vs frequência (com legenda) ----
        st.markdown("---")
        st.subheader("Desempenho vs Frequência (cada ponto = aluno)")
        if len(df_f) == 0:
            st.info("Sem dados para scatter.")
        else:
            if PLOTLY_AVAILABLE:
                fig_sf = px.scatter(df_f, x='frequencia', y='desempenho', color='dominante_emocao', hover_data=['id_aluno','regiao'], color_discrete_sequence=px.colors.qualitative.Set2)
                fig_sf.update_layout(xaxis_title='Frequência (%)', yaxis_title='Desempenho (%)', legend_title='Emoção')
                st.plotly_chart(fig_sf, use_container_width=True)
            else:
                st.dataframe(df_f[['frequencia','desempenho','dominante_emocao']].head(300))

        # ---- Download filtrado ----
        st.markdown("---")
        st.download_button("📥 Download CSV filtrado", df_f.to_csv(index=False).encode('utf-8'), "alunos_emocoes_filtrado.csv", "text/csv")

    except FileNotFoundError:
        st.error("Arquivo 'alunos_emocoes_1000.csv' não encontrado.")
    except Exception as e:
        st.error("Erro ao gerar visualizações.")
        st.exception(e)

elif pagina == "Futuras Expansões":
    st.header("Futuras Expansões")
    st.write("""
    - Integrar GeoJSON com polígonos reais do ES e usar choropleth/heatmap.
    - Adicionar upload de CSV pelo usuário.
    - Modelagem preditiva para risco de evasão a partir de emoções.
    """)
