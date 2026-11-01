
import streamlit as st
import pandas as pd

from services.usuario_service import (
    listar_usuarios,
    criar_usuario,
    atualizar_usuario,
    excluir_usuario
)

from database.erros import ErroAplicacao


def mostrar_usuarios():

    st.title("👥 Gerenciamento de usuários")
    st.write("Cadastre, consulte, edite e exclua usuários da plataforma.")

    st.divider()

    # Consulta os usuários no banco de dados
    try:
        usuarios = listar_usuarios()

    except Exception as erro:
        st.error(f"Não foi possível consultar os usuários: {erro}")
        st.info(
            "Verifique se o MySQL está disponível e se o banco "
            "de dados foi configurado."
        )
        return

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

    # Filtra os usuários
    usuarios_filtrados = [
        usuario for usuario in usuarios
        if busca.lower() in usuario["nome"].lower()
        or busca.lower() in usuario["email"].lower()
    ]

    if usuarios_filtrados:

        df = pd.DataFrame(usuarios_filtrados)

        df = df[["id_usuario", "nome", "email"]]

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

            else:
                try:
                    criar_usuario(nome, email)

                    st.success("Usuário cadastrado com sucesso!")
                    st.rerun()

                except ErroAplicacao as erro:
                    st.error(str(erro))

                except Exception as erro:
                    st.error(f"Erro ao cadastrar usuário: {erro}")

    st.divider()

    # Edição
    st.subheader("✏️ Editar usuário")

    if usuarios:

        usuarios_por_id = {
            usuario["id_usuario"]: usuario
            for usuario in usuarios
        }

        ids = list(usuarios_por_id.keys())

        usuario_selecionado = st.selectbox(
            "Selecione o usuário",
            ids,
            format_func=lambda id: (
                f'{usuarios_por_id[id]["nome"]} '
                f'(ID: {id})'
            ),
            key="usuario_editar"
        )

        usuario = usuarios_por_id[usuario_selecionado]

        with st.form("form_edicao"):

            novo_nome = st.text_input(
                "Nome",
                value=usuario["nome"],
                key=f"editar_nome_{usuario_selecionado}"
            )

            novo_email = st.text_input(
                "E-mail",
                value=usuario["email"],
                key=f"editar_email_{usuario_selecionado}"
            )

            salvar = st.form_submit_button(
                "Salvar alterações",
                use_container_width=True
            )

            if salvar:

                if not novo_nome.strip() or not novo_email.strip():
                    st.error("Preencha todos os campos.")

                else:
                    try:
                        atualizar_usuario(
                            usuario_selecionado,
                            novo_nome,
                            novo_email
                        )

                        st.success("Usuário atualizado com sucesso!")
                        st.rerun()

                    except ErroAplicacao as erro:
                        st.error(str(erro))

                    except Exception as erro:
                        st.error(f"Erro ao atualizar usuário: {erro}")

    else:
        st.info("Não existem usuários para editar.")

    st.divider()

    # Exclusão
    st.subheader("🗑️ Excluir usuário")

    if usuarios:

        usuario_excluir = st.selectbox(
            "Selecione o usuário que deseja excluir",
            ids,
            format_func=lambda id: (
                f'{usuarios_por_id[id]["nome"]} '
                f'(ID: {id})'
            ),
            key="usuario_excluir"
        )

        confirmar = st.checkbox(
            "Confirmo que desejo excluir este usuário.",
            key="confirmar_exclusao_usuario"
        )

        if st.button("Excluir usuário", use_container_width=True):

            if confirmar:

                try:
                    excluir_usuario(usuario_excluir)

                    st.success("Usuário excluído com sucesso!")
                    st.rerun()

                except ErroAplicacao as erro:
                    st.error(str(erro))

                except Exception as erro:
                    st.error(f"Erro ao excluir usuário: {erro}")

            else:
                st.warning("Marque a confirmação antes de excluir.")

    else:
        st.info("Não existem usuários para excluir.")
