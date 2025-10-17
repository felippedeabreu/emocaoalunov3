import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(
    page_title="Análise de Emoções em Alunos",
    page_icon="📊",
    layout="wide"
)

# Menu lateral
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Escolha uma seção:", 
                          ["Introdução", "Base de Dados", "Visualizações", "Futuras Expansões"])

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

    st.write("No futuro, os dados coletados de alunos reais poderão ser integrados.")

    try:
        df = pd.read_csv("alunos_emocoes_100.csv")

        st.subheader("Filtro por Emoção")
        emocoes_disponiveis = df["expressao"].unique().tolist()
        emocao_selecionada = st.selectbox("Selecione uma emoção:", ["Todas"] + emocoes_disponiveis)

        # Aplica o filtro
        if emocao_selecionada == "Todas":
            df_filtrado = df
        else:
            df_filtrado = df[df["expressao"] == emocao_selecionada]

        st.markdown("---")
        st.subheader("Exemplo de Base de Dados")
        st.dataframe(df_filtrado, use_container_width=True)

        st.markdown("---")
        st.subheader("Distribuição das Emoções")

        # Contagem das emoções
        contagem_emocoes = df_filtrado["expressao"].value_counts().reset_index()
        contagem_emocoes.columns = ["Emoção", "Frequência"]

        # ----------------------------------------------------------
        # NOVO: Escolha do tipo de gráfico
        # ----------------------------------------------------------
        tipo_grafico = st.radio(
            "Escolha o tipo de gráfico:",
            ["📊 Gráfico de Barras", "🥧 Gráfico de Pizza", "🎨 Ambos"],
            horizontal=True
        )

        # Exibe gráfico de barras
        if tipo_grafico in ["📊 Gráfico de Barras", "🎨 Ambos"]:
            st.markdown("### 📊 Gráfico de Barras das Emoções")
            st.bar_chart(contagem_emocoes.set_index("Emoção"))

        # Exibe gráfico de pizza
        if tipo_grafico in ["🥧 Gráfico de Pizza", "🎨 Ambos"]:
            st.markdown("### 🥧 Gráfico de Pizza das Emoções")

            fig, ax = plt.subplots(figsize=(6, 6))
            cores = plt.cm.Set3.colors  # Paleta de cores agradável
            ax.pie(
                contagem_emocoes["Frequência"],
                labels=contagem_emocoes["Emoção"],
                autopct="%1.1f%%",
                startangle=90,
                colors=cores,
            )
            ax.axis("equal")  # Deixa o círculo perfeito
            plt.legend(contagem_emocoes["Emoção"], title="Emoções", loc="best")
            st.pyplot(fig)
        # ----------------------------------------------------------

        st.markdown("---")
        st.subheader("Estatísticas Descritivas da Base de Dados")
        st.dataframe(df_filtrado.describe(), use_container_width=True)

    except Exception as e:
        st.warning("⚠️ Não foi possível carregar o dataset. Verifique se o arquivo 'alunos_emocoes_100.csv' está na pasta correta.")
        st.text(e)

# ---------------------------
# Página: Visualizações
# ---------------------------
elif pagina == "Visualizações":
    st.header("Visualizações")

    with st.container():
        st.write("Aqui serão apresentados gráficos interativos, por exemplo:")
        st.bar_chart({"Feliz": 12, "Triste": 5, "Medo": 3, "Neutro": 20, "Nojo": 2, "Nervoso": 8})

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
