import streamlit as st
from components.usuarios import mostrar_usuarios
from components.catalogo import mostrar_catalogo
from components.assinaturas import mostrar_assinaturas
from components.historico import mostrar_historico

# Configuração da página
st.set_page_config(
    page_title="StreamHub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Identidade visual da barra lateral
st.sidebar.title("🎬 StreamHub")
st.sidebar.caption("Sistema de gerenciamento")

st.sidebar.divider()

# Navegação
pagina = st.sidebar.radio(
    "MENU PRINCIPAL",
    [
        "Visão geral",
        "Usuários",
        "Catálogo",
        "Assinaturas",
        "Histórico"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Projeto acadêmico - 2026")

# Conteúdo das páginas
if pagina == "Visão geral":

    st.title("📊 Visão geral")
    st.write("Bem-vindo ao painel administrativo do StreamHub!")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Usuários", "1.250")
    col2.metric("Conteúdos", "340")
    col3.metric("Reproduções", "8.420")
    col4.metric("Assinaturas ativas", "980")

    st.divider()

    st.subheader("Atividade da plataforma")

    st.info("Aqui ficará o gráfico de atividade da plataforma.")

elif pagina == "Usuários":
    mostrar_usuarios()

elif pagina == "Catálogo":
    mostrar_catalogo()

elif pagina == "Assinaturas":
    mostrar_assinaturas()

elif pagina == "Histórico":
    mostrar_historico()
