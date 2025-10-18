import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(
    page_title="Análise de Emoções em Alunos",
    page_icon="📊",
    layout="wide"
)

# ---------------------------
# Menu lateral
# ---------------------------
st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Escolha uma seção:",
    ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"]
)

# ---------------------------
# Página: Introdução (mantida original)
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

    try:
        df = pd.read_csv("alunos_emocoes_1000.csv")

        st.subheader("Filtros")
        col1, col2 = st.columns(2)

        with col1:
            emocao_selecionada = st.selectbox("Selecione uma emoção:", ["Todas"] + sorted(df["dominante_emocao"].unique().tolist()))
        with col2:
            regiao_selecionada = st.selectbox("Selecione uma região:", ["Todas"] + sorted(df["regiao"].unique().tolist()))

        df_filtrado = df.copy()
        if emocao_selecionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["dominante_emocao"] == emocao_selecionada]
        if regiao_selecionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["regiao"] == regiao_selecionada]

        st.markdown("---")
        st.subheader("Visualização da Base de Dados")
        st.dataframe(df_filtrado, use_container_width=True)

        st.markdown("---")
        st.subheader("Estatísticas Descritivas")
        st.dataframe(df_filtrado.describe(), use_container_width=True)

    except Exception as e:
        st.warning("⚠️ Não foi possível carregar o dataset. Verifique se o arquivo 'alunos_emocoes_1000.csv' está na pasta correta.")
        st.text(e)

# ---------------------------
# Página: Visualizações
# ---------------------------
elif pagina == "Visualizações":
    st.header("Visualizações Interativas")

    try:
        df = pd.read_csv("alunos_emocoes_1000.csv")

        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            emocao_filtro = st.selectbox("Filtrar por emoção:", ["Todas"] + sorted(df["dominante_emocao"].unique()))
        with col2:
            regiao_filtro = st.selectbox("Filtrar por região:", ["Todas"] + sorted(df["regiao"].unique()))

        df_f = df.copy()
        if emocao_filtro != "Todas":
            df_f = df_f[df_f["dominante_emocao"] == emocao_filtro]
        if regiao_filtro != "Todas":
            df_f = df_f[df_f["regiao"] == regiao_filtro]

        # ---------------------------
        # Mapa
        # ---------------------------
        st.markdown("### 🗺️ Mapa das Emoções por Região (Espírito Santo)")
        fig_mapa = px.scatter_mapbox(
            df_f,
            lat="lat",
            lon="lon",
            color="dominante_emocao",
            hover_data=["id_aluno", "regiao", "frequencia", "desempenho"],
            zoom=7,
            height=550,
            mapbox_style="carto-positron",
            title="Distribuição Geográfica das Emoções"
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
            fig_bar = px.bar(contagem_emocoes, x="Emoção", y="Frequência", color="Emoção",
                             text_auto=True, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_bar, use_container_width=True)
        with col4:
            fig_pie = px.pie(contagem_emocoes, names="Emoção", values="Frequência",
                             color_discrete_sequence=px.colors.qualitative.Set3, hole=0.3)
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Gráfico de dispersão
        # ---------------------------
        st.subheader("Scatter: Desempenho x Frequência (colorido por emoção)")
        fig_s = px.scatter(df_f, x='frequencia', y='desempenho',
                           color='dominante_emocao', hover_data=['id_aluno','regiao'],
                           color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_s, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Gráfico de Coordenadas Paralelas
        # ---------------------------
        st.subheader("Gráfico de Coordenadas Paralelas")
        fig_parallel = px.parallel_coordinates(
            df_f,
            color="desempenho",
            dimensions=['score_feliz', 'score_medo', 'score_nervoso', 'score_neutro', 'score_nojo', 'score_triste', 'frequencia', 'desempenho'],
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title="Relação entre Emoções, Frequência e Desempenho"
        )
        st.plotly_chart(fig_parallel, use_container_width=True)

    except Exception as e:
        st.error("Erro ao gerar visualizações.")
        st.text(e)

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
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(
    page_title="Análise de Emoções em Alunos",
    page_icon="📊",
    layout="wide"
)

# ---------------------------
# Menu lateral
# ---------------------------
st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Escolha uma seção:",
    ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"]
)

# ---------------------------
# Página: Introdução (mantida original)
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

    try:
        df = pd.read_csv("alunos_emocoes_1000.csv")

        st.subheader("Filtros")
        col1, col2 = st.columns(2)

        with col1:
            emocao_selecionada = st.selectbox("Selecione uma emoção:", ["Todas"] + sorted(df["dominante_emocao"].unique().tolist()))
        with col2:
            regiao_selecionada = st.selectbox("Selecione uma região:", ["Todas"] + sorted(df["regiao"].unique().tolist()))

        df_filtrado = df.copy()
        if emocao_selecionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["dominante_emocao"] == emocao_selecionada]
        if regiao_selecionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["regiao"] == regiao_selecionada]

        st.markdown("---")
        st.subheader("Visualização da Base de Dados")
        st.dataframe(df_filtrado, use_container_width=True)

        st.markdown("---")
        st.subheader("Estatísticas Descritivas")
        st.dataframe(df_filtrado.describe(), use_container_width=True)

    except Exception as e:
        st.warning("⚠️ Não foi possível carregar o dataset. Verifique se o arquivo 'alunos_emocoes_1000.csv' está na pasta correta.")
        st.text(e)

# ---------------------------
# Página: Visualizações
# ---------------------------
elif pagina == "Visualizações":
    st.header("Visualizações Interativas")

    try:
        df = pd.read_csv("alunos_emocoes_1000.csv")

        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            emocao_filtro = st.selectbox("Filtrar por emoção:", ["Todas"] + sorted(df["dominante_emocao"].unique()))
        with col2:
            regiao_filtro = st.selectbox("Filtrar por região:", ["Todas"] + sorted(df["regiao"].unique()))

        df_f = df.copy()
        if emocao_filtro != "Todas":
            df_f = df_f[df_f["dominante_emocao"] == emocao_filtro]
        if regiao_filtro != "Todas":
            df_f = df_f[df_f["regiao"] == regiao_filtro]

        # ---------------------------
        # Mapa
        # ---------------------------
        st.markdown("### 🗺️ Mapa das Emoções por Região (Espírito Santo)")
        fig_mapa = px.scatter_mapbox(
            df_f,
            lat="lat",
            lon="lon",
            color="dominante_emocao",
            hover_data=["id_aluno", "regiao", "frequencia", "desempenho"],
            zoom=7,
            height=550,
            mapbox_style="carto-positron",
            title="Distribuição Geográfica das Emoções"
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
            fig_bar = px.bar(contagem_emocoes, x="Emoção", y="Frequência", color="Emoção",
                             text_auto=True, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_bar, use_container_width=True)
        with col4:
            fig_pie = px.pie(contagem_emocoes, names="Emoção", values="Frequência",
                             color_discrete_sequence=px.colors.qualitative.Set3, hole=0.3)
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Gráfico de dispersão
        # ---------------------------
        st.subheader("Scatter: Desempenho x Frequência (colorido por emoção)")
        fig_s = px.scatter(df_f, x='frequencia', y='desempenho',
                           color='dominante_emocao', hover_data=['id_aluno','regiao'],
                           color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_s, use_container_width=True)

        st.markdown("---")
        # ---------------------------
        # Gráfico de Coordenadas Paralelas
        # ---------------------------
        st.subheader("Gráfico de Coordenadas Paralelas")
        fig_parallel = px.parallel_coordinates(
            df_f,
            color="desempenho",
            dimensions=['score_feliz', 'score_medo', 'score_nervoso', 'score_neutro', 'score_nojo', 'score_triste', 'frequencia', 'desempenho'],
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title="Relação entre Emoções, Frequência e Desempenho"
        )
        st.plotly_chart(fig_parallel, use_container_width=True)

    except Exception as e:
        st.error("Erro ao gerar visualizações.")
        st.text(e)

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

