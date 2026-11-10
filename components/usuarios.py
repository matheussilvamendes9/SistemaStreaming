import streamlit as st
import pandas as pd

from services.usuario_service import (
    listar_usuarios,
    criar_usuario,
    atualizar_usuario,
    excluir_usuario
)

from database.erros import ErroAplicacao



# FUNÇÕES AUXILIARES DE INTERFACE
# (as classes CSS são definidas no app.py)


def formatar_numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


def cabecalho_pagina(tag, titulo, texto):
    st.markdown(f"""
    <div class="hero">
        <span class="hero-tag">{tag}</span>
        <h1 class="hero-titulo">{titulo}</h1>
        <p class="hero-texto">{texto}</p>
    </div>
    """, unsafe_allow_html=True)


def cartao_indicador(icone, rotulo, valor, detalhe):
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-topo">
            <span class="kpi-rotulo">{rotulo}</span>
            <span class="kpi-icone">{icone}</span>
        </div>
        <div class="kpi-valor">{valor}</div>
        <div class="kpi-detalhe">{detalhe}</div>
    </div>
    """, unsafe_allow_html=True)


def titulo_secao(titulo, subtitulo):
    st.markdown(f"""
    <p class="secao-titulo">{titulo}</p>
    <p class="secao-sub">{subtitulo}</p>
    """, unsafe_allow_html=True)



# PÁGINA


def mostrar_usuarios():

    cabecalho_pagina(
        "GESTÃO",
        "Usuários",
        "Cadastre, consulte, edite e exclua usuários da plataforma."
    )

    # --------------------------------------------------------
    # Consulta os usuários no banco de dados
    # --------------------------------------------------------
    try:
        usuarios = listar_usuarios()

    except Exception as erro:
        st.error(f"Não foi possível consultar os usuários: {erro}")
        st.info(
            "Verifique se o MySQL está disponível e se o banco "
            "de dados foi configurado."
        )
        return

    # --------------------------------------------------------
    # Indicadores
    # --------------------------------------------------------
    dominios = {
        u["email"].split("@")[-1].lower()
        for u in usuarios
        if u.get("email") and "@" in u["email"]
    }

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        cartao_indicador(
            "👥", "Total de usuários",
            formatar_numero(len(usuarios)),
            "Usuários cadastrados na plataforma"
        )

    with col2:
        cartao_indicador(
            "✉️", "Domínios de e-mail",
            formatar_numero(len(dominios)),
            "Provedores diferentes entre os cadastros"
        )

    st.write("")
    st.write("")

    # --------------------------------------------------------
    # Consulta de usuários
    # --------------------------------------------------------
    titulo_secao(
        "Usuários cadastrados",
        "Pesquise por nome ou e-mail."
    )

    with st.container(border=True):

        busca = st.text_input(
            "Pesquisar usuário por nome ou e-mail",
            placeholder="🔍  Digite um nome ou e-mail..."
        )

        usuarios_filtrados = [
            usuario for usuario in usuarios
            if busca.lower() in usuario["nome"].lower()
            or busca.lower() in usuario["email"].lower()
        ]

        if usuarios_filtrados:

            df = pd.DataFrame(usuarios_filtrados)

            df = df[["id_usuario", "nome", "email"]]

            df.columns = ["ID", "Nome", "E-mail"]

            st.caption(
                f"{formatar_numero(len(df))} "
                f"{'resultado' if len(df) == 1 else 'resultados'}"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("Nenhum usuário encontrado.")

    st.write("")

    # --------------------------------------------------------
    # Dados auxiliares
    # --------------------------------------------------------
    usuarios_por_id = {
        usuario["id_usuario"]: usuario
        for usuario in usuarios
    }

    ids = list(usuarios_por_id.keys())

    # --------------------------------------------------------
    # Ações
    # --------------------------------------------------------
    titulo_secao(
        "Ações",
        "Cadastre, edite ou exclua usuários."
    )

    aba_cadastro, aba_edicao, aba_exclusao = st.tabs([
        "➕  Cadastrar",
        "✏️  Editar",
        "🗑️  Excluir"
    ])

    # ========================================================
    # CADASTRO
    # ========================================================
    with aba_cadastro:

        with st.container(border=True):

            st.markdown("**Cadastrar usuário**")

            with st.form("form_cadastro", clear_on_submit=True, border=False):

                col1, col2 = st.columns(2, gap="medium")

                with col1:
                    nome = st.text_input("Nome completo")

                with col2:
                    email = st.text_input("E-mail")

                cadastrar = st.form_submit_button(
                    "Cadastrar usuário",
                    use_container_width=True,
                    type="primary"
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

    # ========================================================
    # EDIÇÃO
    # ========================================================
    with aba_edicao:

        if usuarios:

            with st.container(border=True):

                st.markdown("**Editar usuário**")

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

                with st.form("form_edicao", border=False):

                    col1, col2 = st.columns(2, gap="medium")

                    with col1:
                        novo_nome = st.text_input(
                            "Nome",
                            value=usuario["nome"],
                            key=f"editar_nome_{usuario_selecionado}"
                        )

                    with col2:
                        novo_email = st.text_input(
                            "E-mail",
                            value=usuario["email"],
                            key=f"editar_email_{usuario_selecionado}"
                        )

                    salvar = st.form_submit_button(
                        "Salvar alterações",
                        use_container_width=True,
                        type="primary"
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

    # ========================================================
    # EXCLUSÃO
    # ========================================================
    with aba_exclusao:

        if usuarios:

            with st.container(border=True):

                st.markdown("**Excluir usuário**")

                st.warning(
                    "Esta ação não pode ser desfeita.",
                    icon="⚠️"
                )

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

                if st.button(
                    "Excluir usuário",
                    use_container_width=True,
                    type="primary"
                ):

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