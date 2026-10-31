
import streamlit as st
import pandas as pd


def mostrar_usuarios():

    # Inicializa os dados fictícios apenas na primeira execução
    if "usuarios" not in st.session_state:
        st.session_state.usuarios = [
            {
                "id": 1,
                "nome": "Ana Souza",
                "email": "ana@email.com"
            },
            {
                "id": 2,
                "nome": "Carlos Mendes",
                "email": "carlos@email.com"
            },
            {
                "id": 3,
                "nome": "Mariana Lima",
                "email": "mariana@email.com"
            }
        ]

    st.title("👥 Gerenciamento de usuários")
    st.write("Cadastre, consulte, edite e exclua usuários da plataforma.")

    st.divider()

    usuarios = st.session_state.usuarios

    # Indicadores
    col1, col2 = st.columns(2)

    col1.metric("Total de usuários", len(usuarios))
    col2.metric("Cadastros disponíveis", len(usuarios))

    st.divider()

    # Consulta de usuários
    st.subheader("Usuários cadastrados")

    busca = st.text_input(
        "Pesquisar usuário por nome ou e-mail",
        placeholder="Digite um nome ou e-mail..."
    )

    usuarios_filtrados = [
        usuario for usuario in usuarios
        if busca.lower() in usuario["nome"].lower()
        or busca.lower() in usuario["email"].lower()
    ]

    if usuarios_filtrados:
        df = pd.DataFrame(usuarios_filtrados)
        df.columns = ["ID", "Nome", "E-mail"]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum usuário encontrado.")

    st.divider()

    # Cadastro
    st.subheader("➕ Cadastrar usuário")

    with st.form("form_cadastro", clear_on_submit=True):

        nome = st.text_input("Nome completo")
        email = st.text_input("E-mail")

        cadastrar = st.form_submit_button(
            "Cadastrar usuário",
            use_container_width=True
        )

        if cadastrar:

            if not nome.strip() or not email.strip():
                st.error("Preencha todos os campos.")

            elif "@" not in email or "." not in email:
                st.error("Informe um e-mail válido.")

            elif any(
                u["email"].lower() == email.strip().lower()
                for u in usuarios
            ):
                st.error("Este e-mail já está cadastrado.")

            else:
                novo_id = max(
                    [u["id"] for u in usuarios],
                    default=0
                ) + 1

                st.session_state.usuarios.append({
                    "id": novo_id,
                    "nome": nome.strip(),
                    "email": email.strip()
                })

                st.success("Usuário cadastrado com sucesso!")
                st.rerun()

    st.divider()

    # Edição
    st.subheader("✏️ Editar usuário")

    if usuarios:

        ids = [u["id"] for u in usuarios]

        usuario_selecionado = st.selectbox(
            "Selecione o usuário",
            ids,
            format_func=lambda id: next(
                f'{u["nome"]} (ID: {u["id"]})'
                for u in usuarios if u["id"] == id
            ),
            key="usuario_editar"
        )

        usuario = next(
            u for u in usuarios
            if u["id"] == usuario_selecionado
        )

        with st.form("form_edicao"):

            novo_nome = st.text_input(
                "Nome",
                value=usuario["nome"]
            )

            novo_email = st.text_input(
                "E-mail",
                value=usuario["email"]
            )

            salvar = st.form_submit_button(
                "Salvar alterações",
                use_container_width=True
            )

            if salvar:

                if not novo_nome.strip() or not novo_email.strip():
                    st.error("Preencha todos os campos.")

                elif "@" not in novo_email or "." not in novo_email:
                    st.error("Informe um e-mail válido.")

                elif any(
                    u["email"].lower() == novo_email.strip().lower()
                    and u["id"] != usuario_selecionado
                    for u in usuarios
                ):
                    st.error("Este e-mail já pertence a outro usuário.")

                else:
                    usuario["nome"] = novo_nome.strip()
                    usuario["email"] = novo_email.strip()

                    st.success("Usuário atualizado com sucesso!")
                    st.rerun()

    else:
        st.info("Não existem usuários para editar.")

    st.divider()

    # Exclusão
    st.subheader("🗑️ Excluir usuário")

    if usuarios:

        usuario_excluir = st.selectbox(
            "Selecione o usuário que deseja excluir",
            [u["id"] for u in usuarios],
            format_func=lambda id: next(
                f'{u["nome"]} (ID: {u["id"]})'
                for u in usuarios if u["id"] == id
            ),
            key="usuario_excluir"
        )

        confirmar = st.checkbox(
            "Confirmo que desejo excluir este usuário."
        )

        if st.button("Excluir usuário", use_container_width=True):

            if confirmar:
                st.session_state.usuarios = [
                    u for u in usuarios
                    if u["id"] != usuario_excluir
                ]

                st.success("Usuário excluído com sucesso!")
                st.rerun()

            else:
                st.warning("Marque a confirmação antes de excluir.")

    else:
        st.info("Não existem usuários para excluir.")
