
import streamlit as st
import pandas as pd

from services.conteudo_service import (
    listar_catalogo,
    obter_conteudo,
    criar_conteudo,
    atualizar_conteudo,
    excluir_conteudo
)

from services.genero_service import listar_generos
from database.erros import ErroAplicacao


def mostrar_catalogo():

    st.title("🎬 Gerenciamento do catálogo")
    st.write("Cadastre, consulte, edite e exclua filmes e séries.")

    try:
        generos = listar_generos()
        conteudos = listar_catalogo()

    except ErroAplicacao as e:
        st.error(str(e))
        return

    except Exception as e:
        st.error(f"Erro ao carregar o catálogo: {e}")
        return

    # Indicadores
    total = len(conteudos)
    filmes = sum(c["tipo"] == "filme" for c in conteudos)
    series = sum(c["tipo"] == "serie" for c in conteudos)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total de conteúdos", total)
    col2.metric("Filmes", filmes)
    col3.metric("Séries", series)

    st.divider()

    # Consulta e filtros
    st.subheader("📚 Conteúdos cadastrados")

    col_busca, col_filtro = st.columns([2, 1])

    with col_busca:
        busca = st.text_input(
            "Pesquisar por título",
            placeholder="Digite o nome do conteúdo..."
        )

    with col_filtro:
        tipo_filtro = st.selectbox(
            "Filtrar por tipo",
            ["Todos", "Filme", "Série"]
        )

    tipo_db = {
        "Todos": None,
        "Filme": "filme",
        "Série": "serie"
    }[tipo_filtro]

    try:
        filtrados = listar_catalogo(
            busca=busca,
            tipo=tipo_db
        )

    except Exception as e:
        st.error(f"Erro ao consultar conteúdos: {e}")
        return

    if filtrados:
        df = pd.DataFrame(filtrados)

        df = df.rename(columns={
            "id_conteudo": "ID",
            "titulo": "Título",
            "tipo": "Tipo",
            "ano_lancamento": "Ano",
            "duracao_minutos": "Duração (min)",
            "generos": "Gêneros"
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
        st.info("Nenhum conteúdo encontrado.")

    st.divider()

    # Cadastro
    st.subheader("➕ Cadastrar conteúdo")

    nomes_generos = [g["nome"] for g in generos]
    mapa_generos = {g["nome"]: g["id_genero"] for g in generos}

    with st.form("form_cadastro_conteudo", clear_on_submit=True):

        titulo = st.text_input("Título")

        col_tipo, col_ano = st.columns(2)

        with col_tipo:
            tipo = st.selectbox(
                "Tipo de conteúdo",
                ["Filme", "Série"],
                key="cadastro_tipo"
            )

        with col_ano:
            ano = st.number_input(
                "Ano de lançamento",
                min_value=1888,
                max_value=2100,
                value=2020,
                step=1,
                key="cadastro_ano"
            )

        duracao = st.number_input(
            "Duração em minutos (obrigatória para filmes)",
            min_value=0,
            max_value=10000,
            value=0,
            step=1,
            help="Para séries, deixe 0 caso não queira informar."
        )

        generos_selecionados = st.multiselect(
            "Gêneros",
            options=nomes_generos,
            help="Você pode selecionar mais de um gênero."
        )

        cadastrar = st.form_submit_button(
            "Cadastrar conteúdo",
            use_container_width=True
        )

        if cadastrar:

            if not titulo.strip():
                st.error("Informe o título do conteúdo.")

            elif tipo == "Filme" and duracao <= 0:
                st.error("Informe a duração do filme.")

            elif not generos:
                st.error("Não existem gêneros cadastrados no banco.")

            else:
                try:
                    ids = [
                        mapa_generos[nome]
                        for nome in generos_selecionados
                    ]

                    criar_conteudo(
                        titulo=titulo,
                        tipo="filme" if tipo == "Filme" else "serie",
                        ano_lancamento=int(ano),
                        duracao_minutos=int(duracao) if duracao > 0 else None,
                        ids_generos=ids
                    )

                    st.success("Conteúdo cadastrado com sucesso!")
                    st.rerun()

                except ErroAplicacao as e:
                    st.error(str(e))

                except Exception as e:
                    st.error(f"Erro ao cadastrar conteúdo: {e}")

    st.divider()

    # Edição
    st.subheader("✏️ Editar conteúdo")

    if conteudos:

        opcoes = {
            f'{c["titulo"]} (ID: {c["id_conteudo"]})': c["id_conteudo"]
            for c in conteudos
        }

        selecionado = st.selectbox(
            "Selecione o conteúdo",
            list(opcoes.keys()),
            key="conteudo_editar"
        )

        id_editar = opcoes[selecionado]

        conteudo = obter_conteudo(id_editar)

        tipo_atual = conteudo["tipo"]
        duracao_atual = conteudo["duracao_minutos"] or 0

        generos_atuais = [
            g["nome"]
            for g in generos
            if g["id_genero"] in conteudo["ids_generos"]
        ]

        with st.form("form_edicao_conteudo"):

            novo_titulo = st.text_input(
                "Título",
                value=conteudo["titulo"]
            )

            col_tipo, col_ano = st.columns(2)

            with col_tipo:
                novo_tipo = st.selectbox(
                    "Tipo",
                    ["Filme", "Série"],
                    index=0 if tipo_atual == "filme" else 1
                )

            with col_ano:
                novo_ano = st.number_input(
                    "Ano de lançamento",
                    min_value=1888,
                    max_value=2100,
                    value=int(conteudo["ano_lancamento"]),
                    step=1
                )

            nova_duracao = st.number_input(
                "Duração em minutos (obrigatória para filmes)",
                min_value=0,
                max_value=10000,
                value=int(duracao_atual),
                step=1
            )

            novos_generos = st.multiselect(
                "Gêneros",
                options=nomes_generos,
                default=generos_atuais
            )

            salvar = st.form_submit_button(
                "Salvar alterações",
                use_container_width=True
            )

            if salvar:

                if not novo_titulo.strip():
                    st.error("Informe o título do conteúdo.")

                elif novo_tipo == "Filme" and nova_duracao <= 0:
                    st.error("Informe a duração do filme.")

                else:
                    try:
                        ids = [
                            mapa_generos[nome]
                            for nome in novos_generos
                        ]

                        atualizar_conteudo(
                            id_conteudo=id_editar,
                            titulo=novo_titulo,
                            tipo="filme" if novo_tipo == "Filme" else "serie",
                            ano_lancamento=int(novo_ano),
                            duracao_minutos=int(nova_duracao) if nova_duracao > 0 else None,
                            ids_generos=ids
                        )

                        st.success("Conteúdo atualizado com sucesso!")
                        st.rerun()

                    except ErroAplicacao as e:
                        st.error(str(e))

                    except Exception as e:
                        st.error(f"Erro ao atualizar conteúdo: {e}")

    else:
        st.info("Não existem conteúdos para editar.")

    st.divider()

    # Exclusão
    st.subheader("🗑️ Excluir conteúdo")

    if conteudos:

        id_excluir = st.selectbox(
            "Selecione o conteúdo que deseja excluir",
            list(opcoes.keys()),
            key="conteudo_excluir"
        )

        id_excluir = opcoes[id_excluir]

        confirmar = st.checkbox(
            "Confirmo que desejo excluir este conteúdo."
        )

        if st.button(
            "Excluir conteúdo",
            use_container_width=True
        ):

            if confirmar:
                try:
                    excluir_conteudo(id_excluir)

                    st.success("Conteúdo excluído com sucesso!")
                    st.rerun()

                except ErroAplicacao as e:
                    st.error(str(e))

                except Exception as e:
                    st.error(f"Erro ao excluir conteúdo: {e}")

            else:
                st.warning("Confirme a exclusão antes de continuar.")

    else:
        st.info("Não existem conteúdos para excluir.")
