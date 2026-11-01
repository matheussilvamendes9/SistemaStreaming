
import streamlit as st
import pandas as pd

from services.historico_service import (
    listar_historico,
    excluir_reproducao
)

from database.erros import ErroAplicacao


def mostrar_historico():

    st.title("Histórico de Reproduções")
    st.write(
        "Consulte e acompanhe as reproduções realizadas pelos usuários."
    )

    # Consulta ao banco de dados
    try:
        historico = listar_historico()

    except ErroAplicacao as e:
        st.error(str(e))
        return

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return

    # Indicadores
    total = len(historico)

    tempo_total = sum(
        int(h["progresso_minutos"] or 0)
        for h in historico
    )

    conteudos_unicos = len({
        h["conteudo"] for h in historico
    })

    col1, col2, col3 = st.columns(3)

    col1.metric("Total de reproduções", total)
    col2.metric("Tempo assistido", f"{tempo_total} min")
    col3.metric("Conteúdos reproduzidos", conteudos_unicos)

    st.divider()

    # Listagem e filtros
    st.subheader("Reproduções registradas")

    col1, col2 = st.columns(2)

    with col1:
        pesquisa = st.text_input(
            "Pesquisar",
            placeholder="Usuário ou conteúdo..."
        )

    with col2:
        filtro_tipo = st.selectbox(
            "Tipo de conteúdo",
            ["Todos", "Filme", "Série"]
        )

    historico_filtrado = historico.copy()

    # Pesquisa por usuário ou conteúdo
    if pesquisa.strip():

        historico_filtrado = [
            h for h in historico_filtrado
            if pesquisa.lower() in h["usuario"].lower()
            or pesquisa.lower() in h["conteudo"].lower()
        ]

    # Filtro por tipo
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

        df = df.rename(columns={
            "id_reproducao": "ID",
            "usuario": "Usuário",
            "conteudo": "Conteúdo",
            "tipo": "Tipo",
            "data_hora": "Data e horário",
            "progresso_minutos": "Minutos assistidos"
        })

        df["Tipo"] = df["Tipo"].map({
            "filme": "Filme",
            "serie": "Série"
        })

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Nenhuma reprodução encontrada.")

    st.divider()

    # Gráfico de conteúdos mais reproduzidos
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

    # Exclusão de reprodução
    st.subheader("Excluir reprodução")

    if historico:

        opcoes = {
            (
                f'ID {h["id_reproducao"]} - '
                f'{h["usuario"]} - {h["conteudo"]}'
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
