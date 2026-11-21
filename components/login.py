
import streamlit as st

from mocks.auth_mock import fazer_login


def mostrar_login():
    """
    Exibe a tela de login do StreamHub.
    """

    st.title("StreamHub")
    st.caption("Entre na sua conta para continuar.")

    st.divider()

    # Centraliza o formulário na página.
    _, coluna, _ = st.columns([1, 2, 1])

    with coluna:
        with st.form("formulario_login"):
            st.subheader("Acessar conta")

            email = st.text_input(
                "E-mail",
                placeholder="Digite seu e-mail"
            )

            senha = st.text_input(
                "Senha",
                type="password",
                placeholder="Digite sua senha"
            )

            entrar = st.form_submit_button(
                "Entrar",
                use_container_width=True
            )

            if entrar:
                if not email or not senha:
                    st.warning("Preencha o e-mail e a senha.")
                    return

                try:
                    resultado = fazer_login(email, senha)

                    st.session_state["token"] = resultado["access_token"]
                    st.session_state["usuario"] = resultado["usuario"]
                    st.session_state["autenticado"] = True

                    st.rerun()

                except ValueError as erro:
                    st.error(str(erro))
