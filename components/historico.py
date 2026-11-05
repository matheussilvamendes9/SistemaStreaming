
import streamlit as st
import pandas as pd

from services.historico_service import (
    listar_historico,
    registrar_reproducao,
    excluir_reproducao
)

from services.usuario_service import listar_usuarios
from services.conteudo_service import listar_catalogo
from services.episodio_service import listar_episodios

from database.erros import ErroAplicacao


def mostrar_historico():

    st.title("Histórico de Reproduções")
    st.write(
        "Consulte, registre e acompanhe as reproduções realizadas pelos usuários."
    )

    # Consulta ao banco de dados
    try:
        historico = listar_historico()
        usuarios = listar_usuarios()
        catalogo = listar_catalogo()
        episodios = listar_episodios()

    except ErroAplicacao as e:
        st.error(str(e))
        return

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return

    # =====================================================
    # CADASTRO DE REPRODUÇÃO
    # =====================================================

    st.subheader("Registrar reprodução")

    if not usuarios:
        st.warning("Cadastre pelo menos um usuário antes de registrar reproduções.")

    elif not catalogo:
        st.warning("Cadastre pelo menos um filme ou série no catálogo.")

    else:

        usuarios_por_id = {
            u["id_usuario"]: u for u in usuarios
        }

        conteudos_por_id = {
            c["id_conteudo"]: c for c in catalogo
        }

        episodios_disponiveis = []

        with st.container():

            col1, col2 = st.columns(2)

            with col1:
                id_usuario = st.selectbox(
                    "Usuário",
                    list(usuarios_por_id.keys()),
                    format_func=lambda id: (
                        f'{usuarios_por_id[id]["nome"]} '
                        f'(ID: {id})'
                    ),
                    key="historico_usuario"
                )

            with col2:
                id_conteudo = st.selectbox(
                    "Conteúdo",
                    list(conteudos_por_id.keys()),
                    format_func=lambda id: (
                        f'{conteudos_por_id[id]["titulo"]} '
                        f'({"Filme" if conteudos_por_id[id]["tipo"] == "filme" else "Série"})'
                    ),
                    key="historico_conteudo"
                )

            conteudo = conteudos_por_id[id_conteudo]

            id_episodio = None
            duracao = conteudo["duracao_minutos"]

            if conteudo["tipo"] == "serie":

                episodios_disponiveis = [
                    e for e in episodios
                    if e["id_serie"] == id_conteudo
                ]

                if episodios_disponiveis:

                    episodios_por_id = {
                        e["id_episodio"]: e
                        for e in episodios_disponiveis
                    }

                    id_episodio = st.selectbox(
                        "Episódio",
                        list(episodios_por_id.keys()),
                        format_func=lambda id: (
                            f'Temporada {episodios_por_id[id]["temporada"]} - '
                            f'Episódio {episodios_por_id[id]["episodio"]}: '
                            f'{episodios_por_id[id]["titulo"]}'
                        ),
                        key=f"historico_episodio_{id_conteudo}"
                    )

                    duracao = episodios_por_id[id_episodio]["duracao_minutos"]

                else:
                    st.warning(
                        "Esta série ainda não possui episódios cadastrados."
                    )
            progresso = None
            
            if duracao is not None:
                progresso = st.number_input(
                    "Minutos assistidos",
                    min_value=0.0,
                    max_value=float(duracao),
                    value=0.0,
                    step=1.0,
                    key="historico_progresso"
                )
            else:
                st.info(
                    "Não foi possível identificar a duração. "
                    "Verifique o cadastro do conteúdo ou do episódio."
                )
            pode_registrar = (
                conteudo["tipo"] == "filme"
                or bool(episodios_disponiveis)
            )

            if st.button(
                "Registrar reprodução",
                use_container_width=True,
                disabled=not pode_registrar
            ):

                try:
                    registrar_reproducao(
                        id_usuario=id_usuario,
                        id_conteudo=id_conteudo,
                        id_episodio=id_episodio,
                        progresso_minutos=progresso
                    )

                    st.success("Reprodução registrada com sucesso!")
                    st.rerun()

                except ErroAplicacao as e:
                    st.error(str(e))

                except Exception as e:
                    st.error(f"Erro ao registrar reprodução: {e}")

    st.divider()

    # =====================================================
    # INDICADORES
    # =====================================================

    total = len(historico)

    tempo_total = sum(
        float(h["progresso_minutos"] or 0)
        for h in historico
    )

    conteudos_unicos = len({
        h["conteudo"] for h in historico
    })

    col1, col2, col3 = st.columns(3)

    col1.metric("Total de reproduções", total)
    col2.metric("Tempo assistido", f"{tempo_total:g} min")
    col3.metric("Conteúdos reproduzidos", conteudos_unicos)

    st.divider()

    # =====================================================
    # LISTAGEM E FILTROS
    # =====================================================

    st.subheader("Reproduções registradas")

    col1, col2 = st.columns(2)

    with col1:
        pesquisa = st.text_input(
            "Pesquisar",
            placeholder="Usuário, conteúdo ou episódio..."
        )

    with col2:
        filtro_tipo = st.selectbox(
            "Tipo de conteúdo",
            ["Todos", "Filme", "Série"]
        )

    historico_filtrado = historico.copy()

    if pesquisa.strip():

        termo = pesquisa.lower()

        historico_filtrado = [
            h for h in historico_filtrado
            if termo in h["usuario"].lower()
            or termo in h["conteudo"].lower()
            or termo in (h["titulo_episodio"] or "").lower()
        ]

    if filtro_tipo != "Todos":

        tipo_db = {
            "Filme": "filme",
            "Série": "serie"
        }[filtro_tipo]

        historico_filtrado = [
            h for h in historico_filtrado
            if h["tipo"] == tipo_db
        ]

    if historico_filtrado:

        df = pd.DataFrame(historico_filtrado)

        df["data_hora"] = pd.to_datetime(
            df["data_hora"]
        ).dt.strftime("%d/%m/%Y %H:%M")

        def identificar_episodio(linha):
            if linha["tipo"] == "filme":
                return "-"

            if pd.isna(linha["episodio"]):
                return "Episódio não identificado"

            return (
                f'T{int(linha["temporada"])} '
                f'E{int(linha["episodio"])} - '
                f'{linha["titulo_episodio"]}'
            )

        df["episodio_exibicao"] = df.apply(
            identificar_episodio,
            axis=1
        )

        df["tipo"] = df["tipo"].map({
            "filme": "Filme",
            "serie": "Série"
        })

        df = df[[
            "id_reproducao",
            "usuario",
            "conteudo",
            "tipo",
            "episodio_exibicao",
            "data_hora",
            "progresso_minutos"
        ]]

        df = df.rename(columns={
            "id_reproducao": "ID",
            "usuario": "Usuário",
            "conteudo": "Conteúdo",
            "tipo": "Tipo",
            "episodio_exibicao": "Episódio",
            "data_hora": "Data e horário",
            "progresso_minutos": "Minutos assistidos"
        })

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Nenhuma reprodução encontrada.")

    st.divider()

    # =====================================================
    # GRÁFICO
    # =====================================================

    st.subheader("Conteúdos mais reproduzidos")

    if historico:

        df_grafico = pd.DataFrame(historico)

        reproducoes = (
            df_grafico.groupby("conteudo")
            .size()
            .reset_index(name="Reproduções")
            .sort_values("Reproduções", ascending=False)
        )

        reproducoes = reproducoes.set_index("conteudo")

        st.bar_chart(reproducoes)

    else:
        st.info(
            "Ainda não existem reproduções para visualizar."
        )

    st.divider()

    # =====================================================
    # EXCLUSÃO
    # =====================================================

    st.subheader("Excluir reprodução")

    if historico:

        opcoes = {
            (
                f'ID {h["id_reproducao"]} - '
                f'{h["usuario"]} - {h["conteudo"]}'
                + (
                    f' - {h["titulo_episodio"]}'
                    if h["titulo_episodio"]
                    else ""
                )
            ): h["id_reproducao"]
            for h in historico
        }

        reproducao_selecionada = st.selectbox(
            "Selecione a reprodução",
            list(opcoes.keys()),
            key="excluir_historico"
        )

        id_excluir = opcoes[reproducao_selecionada]

        confirmar = st.checkbox(
            "Confirmo que desejo excluir esta reprodução.",
            key="confirmar_exclusao_historico"
        )

        if st.button(
            "Excluir reprodução",
            type="primary"
        ):

            if confirmar:

                try:
                    excluir_reproducao(id_excluir)

                    st.success(
                        "Reprodução excluída com sucesso!"
                    )

                    st.rerun()

                except ErroAplicacao as e:
                    st.error(str(e))

                except Exception as e:
                    st.error(
                        f"Erro ao excluir reprodução: {e}"
                    )

            else:
                st.warning(
                    "Marque a confirmação antes de excluir."
                )

    else:
        st.info(
            "Não existem reproduções para excluir."
        )
