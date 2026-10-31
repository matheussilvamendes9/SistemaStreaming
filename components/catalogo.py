
import streamlit as st
import pandas as pd


def mostrar_catalogo():

    # Dados fictícios iniciais
    if "conteudos" not in st.session_state:
        st.session_state.conteudos = [
            {
                "id": 1,
                "titulo": "Interestelar",
                "tipo": "Filme",
                "ano": 2014,
                "genero": "Ficção científica"
            },
            {
                "id": 2,
                "titulo": "Breaking Bad",
                "tipo": "Série",
                "ano": 2008,
                "genero": "Drama"
            },
            {
                "id": 3,
                "titulo": "A Origem",
                "tipo": "Filme",
                "ano": 2010,
                "genero": "Ficção científica"
            },
            {
                "id": 4,
                "titulo": "Dark",
                "tipo": "Série",
                "ano": 2017,
                "genero": "Suspense"
            }
        ]

    st.title("🎬 Gerenciamento do catálogo")
    st.write("Cadastre, consulte, edite e exclua filmes e séries.")

    conteudos = st.session_state.conteudos

    st.divider()

    # Indicadores
    total = len(conteudos)
    filmes = sum(c["tipo"] == "Filme" for c in conteudos)
    series = sum(c["tipo"] == "Série" for c in conteudos)

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

    filtrados = [
        c for c in conteudos
        if busca.lower() in c["titulo"].lower()
        and (
            tipo_filtro == "Todos"
            or c["tipo"] == tipo_filtro
        )
    ]

    if filtrados:
        df = pd.DataFrame(filtrados)
        df.columns = ["ID", "Título", "Tipo", "Ano", "Gênero"]

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

    with st.form("form_cadastro_conteudo", clear_on_submit=True):

        titulo = st.text_input("Título")

        col_tipo, col_ano = st.columns(2)

        with col_tipo:
            tipo = st.selectbox(
                "Tipo de conteúdo",
                ["Filme", "Série"]
            )

        with col_ano:
            ano = st.number_input(
                "Ano de lançamento",
                min_value=1888,
                max_value=2100,
                value=2020,
                step=1
            )

        genero = st.selectbox(
            "Gênero",
            [
                "Ação",
                "Aventura",
                "Comédia",
                "Drama",
                "Ficção científica",
                "Romance",
                "Suspense",
                "Terror"
            ]
        )

        cadastrar = st.form_submit_button(
            "Cadastrar conteúdo",
            use_container_width=True
        )

        if cadastrar:

            if not titulo.strip():
                st.error("Informe o título do conteúdo.")

            elif any(
                c["titulo"].lower() == titulo.strip().lower()
                for c in conteudos
            ):
                st.error("Este conteúdo já está cadastrado.")

            else:
                novo_id = max(
                    [c["id"] for c in conteudos],
                    default=0
                ) + 1

                st.session_state.conteudos.append({
                    "id": novo_id,
                    "titulo": titulo.strip(),
                    "tipo": tipo,
                    "ano": int(ano),
                    "genero": genero
                })

                st.success("Conteúdo cadastrado com sucesso!")
                st.rerun()

    st.divider()

    # Edição
    st.subheader("✏️ Editar conteúdo")

    if conteudos:

        id_editar = st.selectbox(
            "Selecione o conteúdo",
            [c["id"] for c in conteudos],
            format_func=lambda id: next(
                f'{c["titulo"]} (ID: {c["id"]})'
                for c in conteudos if c["id"] == id
            ),
            key="conteudo_editar"
        )

        conteudo = next(
            c for c in conteudos if c["id"] == id_editar
        )

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
                    index=["Filme", "Série"].index(conteudo["tipo"])
                )

            with col_ano:
                novo_ano = st.number_input(
                    "Ano de lançamento",
                    min_value=1888,
                    max_value=2100,
                    value=conteudo["ano"],
                    step=1
                )

            generos = [
                "Ação",
                "Aventura",
                "Comédia",
                "Drama",
                "Ficção científica",
                "Romance",
                "Suspense",
                "Terror"
            ]

            novo_genero = st.selectbox(
                "Gênero",
                generos,
                index=generos.index(conteudo["genero"])
            )

            salvar = st.form_submit_button(
                "Salvar alterações",
                use_container_width=True
            )

            if salvar:

                if not novo_titulo.strip():
                    st.error("Informe o título do conteúdo.")

                elif any(
                    c["titulo"].lower() == novo_titulo.strip().lower()
                    and c["id"] != id_editar
                    for c in conteudos
                ):
                    st.error("Já existe outro conteúdo com esse título.")

                else:
                    conteudo["titulo"] = novo_titulo.strip()
                    conteudo["tipo"] = novo_tipo
                    conteudo["ano"] = int(novo_ano)
                    conteudo["genero"] = novo_genero

                    st.success("Conteúdo atualizado com sucesso!")
                    st.rerun()

    else:
        st.info("Não existem conteúdos para editar.")

    st.divider()

    # Exclusão
    st.subheader("🗑️ Excluir conteúdo")

    if conteudos:

        id_excluir = st.selectbox(
            "Selecione o conteúdo que deseja excluir",
            [c["id"] for c in conteudos],
            format_func=lambda id: next(
                f'{c["titulo"]} (ID: {c["id"]})'
                for c in conteudos if c["id"] == id
            ),
            key="conteudo_excluir"
        )

        confirmar = st.checkbox(
            "Confirmo que desejo excluir este conteúdo."
        )

        if st.button(
            "Excluir conteúdo",
            use_container_width=True
        ):

            if confirmar:
                st.session_state.conteudos = [
                    c for c in conteudos
                    if c["id"] != id_excluir
                ]

                st.success("Conteúdo excluído com sucesso!")
                st.rerun()

            else:
                st.warning("Confirme a exclusão antes de continuar.")

    else:
        st.info("Não existem conteúdos para excluir.")
