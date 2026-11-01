
import streamlit as st
import pandas as pd

from components.usuarios import mostrar_usuarios
from components.catalogo import mostrar_catalogo
from components.assinaturas import mostrar_assinaturas
from components.historico import mostrar_historico

from services.indicadores_service import obter_indicadores
from database.erros import ErroAplicacao


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
    st.write(
        "Bem-vindo ao painel administrativo do StreamHub!"
    )

    # Consulta dos indicadores no banco de dados
    try:
        indicadores = obter_indicadores()

        total_conteudos = (
            indicadores["total_filmes"]
            + indicadores["total_series"]
        )

        # Indicadores principais
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Usuários",
            indicadores["total_usuarios"]
        )

        col2.metric(
            "Conteúdos",
            total_conteudos,
            help=(
                f'{indicadores["total_filmes"]} filmes e '
                f'{indicadores["total_series"]} séries'
            )
        )

        col3.metric(
            "Reproduções",
            indicadores["total_reproducoes"]
        )

        col4.metric(
            "Assinaturas ativas",
            indicadores["assinaturas_ativas"]
        )

        st.divider()

        # Gráfico de conteúdos mais reproduzidos
        st.subheader("Conteúdos mais reproduzidos")

        top_conteudos = indicadores["top_conteudos"]

        if top_conteudos:

            df = pd.DataFrame(top_conteudos)

            df = df.rename(columns={
                "titulo": "Conteúdo",
                "total_reproducoes": "Reproduções"
            })

            df = df[["Conteúdo", "Reproduções"]]

            df = df.set_index("Conteúdo")

            st.bar_chart(
                df,
                use_container_width=True
            )

        else:
            st.info(
                "Ainda não existem conteúdos cadastrados."
            )

    except ErroAplicacao as e:
        st.error(str(e))

    except Exception as e:
        st.error(
            f"Não foi possível carregar a visão geral: {e}"
        )


elif pagina == "Usuários":
    mostrar_usuarios()

elif pagina == "Catálogo":
    mostrar_catalogo()

elif pagina == "Assinaturas":
    mostrar_assinaturas()

elif pagina == "Histórico":
    mostrar_historico()
