import streamlit as st
import pandas as pd
from datetime import date, timedelta

from services.assinatura_service import (
    listar_assinaturas,
    criar_assinatura,
    atualizar_assinatura,
    encerrar_assinatura,
    excluir_assinatura
)

from services.plano_service import listar_planos
from services.usuario_service import listar_usuarios
from database.erros import ErroAplicacao


STATUS = {
    "Ativa": "ativa",
    "Cancelada": "cancelada",
    "Expirada": "expirada"
}

ROTULO_STATUS = {
    "ativa": "🟢 Ativa",
    "cancelada": "🔴 Cancelada",
    "expirada": "🟠 Expirada"
}



# FUNÇÕES AUXILIARES DE INTERFACE
# (as classes CSS são definidas no app.py)


def formatar_numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


def formatar_moeda(valor):
    return f"R$ {float(valor):.2f}".replace(".", ",")


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


def caixa_valor(valor):
    """Destaque do valor da assinatura."""
    st.markdown(f"""
    <div class="rank-item" style="margin-bottom: 14px;">
        <div class="rank-pos">💰</div>
        <div class="rank-nome">Valor da assinatura</div>
        <div class="rank-valor" style="font-size: 16px; color: #F5F6F8;">
            {valor}
        </div>
    </div>
    """, unsafe_allow_html=True)



# PÁGINA


def mostrar_assinaturas():

    cabecalho_pagina(
        "GESTÃO",
        "Assinaturas",
        "Gerencie os planos e as assinaturas dos usuários."
    )

    
    # Carregamento dos dados
    
    try:
        assinaturas = listar_assinaturas()
        usuarios = listar_usuarios()
        planos = listar_planos()

    except ErroAplicacao as e:
        st.error(str(e))
        return

    except Exception as e:
        st.error(f"Erro ao carregar assinaturas: {e}")
        return

    
    # Indicadores
    
    total = len(assinaturas)
    ativas = sum(a["status"] == "ativa" for a in assinaturas)
    canceladas = sum(a["status"] == "cancelada" for a in assinaturas)
    expiradas = sum(a["status"] == "expirada" for a in assinaturas)

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        cartao_indicador(
            "💳", "Total",
            formatar_numero(total),
            "Assinaturas cadastradas"
        )

    with col2:
        cartao_indicador(
            "🟢", "Ativas",
            formatar_numero(ativas),
            "Em vigor atualmente"
        )

    with col3:
        cartao_indicador(
            "🔴", "Canceladas",
            formatar_numero(canceladas),
            "Encerradas por cancelamento"
        )

    with col4:
        cartao_indicador(
            "🟠", "Expiradas",
            formatar_numero(expiradas),
            "Encerradas por expiração"
        )

    st.write("")
    st.write("")

    
    # Consulta e filtros
    
    titulo_secao(
        "Assinaturas cadastradas",
        "Pesquise por usuário ou filtre pelo status da assinatura."
    )

    with st.container(border=True):

        col1, col2 = st.columns([3, 1], gap="medium")

        with col1:
            pesquisa = st.text_input(
                "Pesquisar usuário",
                placeholder="🔍  Digite o nome do usuário..."
            )

        with col2:
            filtro_status = st.selectbox(
                "Filtrar por status",
                ["Todos", "Ativa", "Cancelada", "Expirada"]
            )

        status_db = STATUS.get(filtro_status)

        try:
            assinaturas_filtradas = listar_assinaturas(
                status=status_db
            )

            if pesquisa.strip():
                assinaturas_filtradas = [
                    a for a in assinaturas_filtradas
                    if pesquisa.lower() in a["usuario"].lower()
                ]

        except Exception as e:
            st.error(f"Erro ao consultar assinaturas: {e}")
            return

        if assinaturas_filtradas:

            df = pd.DataFrame(assinaturas_filtradas)

            df = df.rename(columns={
                "id_assinatura": "ID",
                "id_usuario": "ID do usuário",
                "usuario": "Usuário",
                "id_plano": "ID do plano",
                "plano": "Plano",
                "valor": "Valor",
                "data_inicio": "Data de início",
                "data_termino": "Data de término",
                "status": "Status"
            })

            df["Plano"] = df["Plano"].str.title()
            df["Status"] = df["Status"].map(ROTULO_STATUS)
            df["Valor"] = df["Valor"].astype(float)
            df["Data de início"] = pd.to_datetime(df["Data de início"])
            df["Data de término"] = pd.to_datetime(df["Data de término"])

            st.caption(
                f"{formatar_numero(len(df))} "
                f"{'resultado' if len(df) == 1 else 'resultados'}"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Valor": st.column_config.NumberColumn(
                        "Valor",
                        format="R$ %.2f"
                    ),
                    "Data de início": st.column_config.DateColumn(
                        "Data de início",
                        format="DD/MM/YYYY"
                    ),
                    "Data de término": st.column_config.DateColumn(
                        "Data de término",
                        format="DD/MM/YYYY"
                    ),
                }
            )

        else:
            st.info("Nenhuma assinatura encontrada.")

    st.write("")

    
    # Verificação de usuários e planos
    
    if not usuarios:
        st.warning(
            "Não existem usuários cadastrados. "
            "Cadastre um usuário antes de criar uma assinatura."
        )
        return

    if not planos:
        st.warning(
            "Não existem planos cadastrados no banco de dados."
        )
        return

    opcoes_usuarios = {
        f'{u["nome"]} (ID: {u["id_usuario"]})': u["id_usuario"]
        for u in usuarios
    }

    opcoes_planos = {
        f'{p["nome"].title()} - R$ {float(p["valor"]):.2f}': p["id_plano"]
        for p in planos
    }

    planos_por_id = {
        p["id_plano"]: p
        for p in planos
    }

    opcoes_assinaturas = {
        f'ID {a["id_assinatura"]} - {a["usuario"]} '
        f'({a["plano"].title()})': a["id_assinatura"]
        for a in assinaturas
    }

    
    # Ações
    
    titulo_secao(
        "Ações",
        "Cadastre, edite, encerre ou exclua assinaturas."
    )

    aba_cadastro, aba_edicao, aba_encerrar, aba_exclusao = st.tabs([
        "Cadastrar",
        "Editar",
        "Encerrar",
        "Excluir"
    ])

    # ========================================================
    # CADASTRO
    # ========================================================
    with aba_cadastro:

        with st.container(border=True):

            st.markdown("**Cadastrar nova assinatura**")

            plano_novo = st.selectbox(
                "Plano",
                list(opcoes_planos.keys()),
                key="cadastro_plano"
            )

            id_plano_novo = opcoes_planos[plano_novo]
            dados_plano_novo = planos_por_id[id_plano_novo]

            caixa_valor(formatar_moeda(dados_plano_novo["valor"]))

            with st.form("form_cadastro_assinatura", border=False):

                usuario_selecionado = st.selectbox(
                    "Usuário",
                    list(opcoes_usuarios.keys())
                )

                col1, col2, col3 = st.columns(3, gap="medium")

                with col1:
                    data_inicio = st.date_input(
                        "Data de início",
                        value=date.today(),
                        key="cadastro_data_inicio",
                        format="DD/MM/YYYY"
                    )

                with col2:
                    status_selecionado = st.selectbox(
                        "Status",
                        ["Ativa", "Cancelada", "Expirada"],
                        key="cadastro_status"
                    )

                with col3:
                    data_termino = st.date_input(
                        "Data de término",
                        value=date.today() + timedelta(days=30),
                        key="cadastro_data_termino",
                        format="DD/MM/YYYY"
                    )

                st.caption(
                    "Assinaturas ativas não possuem data de término."
                )

                cadastrar = st.form_submit_button(
                    "Cadastrar assinatura",
                    use_container_width=True,
                    type="primary"
                )

                if cadastrar:

                    status_db_novo = STATUS[status_selecionado]

                    # Assinaturas ativas não possuem data de término.
                    termino = (
                        None if status_db_novo == "ativa"
                        else data_termino
                    )

                    if termino and termino < data_inicio:
                        st.error(
                            "A data de término não pode ser anterior "
                            "à data de início."
                        )

                    else:
                        try:
                            criar_assinatura(
                                id_usuario=opcoes_usuarios[usuario_selecionado],
                                id_plano=id_plano_novo,
                                data_inicio=data_inicio,
                                data_termino=termino,
                                status=status_db_novo,
                                valor=None
                            )

                            st.success("Assinatura cadastrada com sucesso!")
                            st.rerun()

                        except ErroAplicacao as e:
                            st.error(str(e))

                        except Exception as e:
                            st.error(f"Erro ao cadastrar assinatura: {e}")

    # ========================================================
    # EDIÇÃO
    # ========================================================
    with aba_edicao:

        if assinaturas:

            with st.container(border=True):

                st.markdown("**Editar assinatura**")

                assinatura_selecionada = st.selectbox(
                    "Selecione a assinatura",
                    list(opcoes_assinaturas.keys()),
                    key="editar_assinatura"
                )

                id_selecionado = opcoes_assinaturas[assinatura_selecionada]

                assinatura = next(
                    a for a in assinaturas
                    if a["id_assinatura"] == id_selecionado
                )

                # Seleção do plano fora do formulário para atualizar
                # o valor apresentado quando o plano for alterado.
                planos_edicao = list(opcoes_planos.keys())

                indice_plano_atual = next(
                    i for i, p in enumerate(planos_edicao)
                    if opcoes_planos[p] == assinatura["id_plano"]
                )

                plano_editado = st.selectbox(
                    "Plano da assinatura",
                    planos_edicao,
                    index=indice_plano_atual,
                    key="edicao_plano"
                )

                id_plano_editado = opcoes_planos[plano_editado]

                # Se o plano não mudou, preservamos o preço contratado.
                # Se mudou, utilizamos o preço atual do novo plano.
                if id_plano_editado == assinatura["id_plano"]:
                    valor_editado = float(assinatura["valor"])
                else:
                    valor_editado = float(
                        planos_por_id[id_plano_editado]["valor"]
                    )

                caixa_valor(formatar_moeda(valor_editado))

                # Conversão segura das datas recebidas do MySQL.
                inicio_atual = pd.to_datetime(
                    assinatura["data_inicio"]
                ).date()

                with st.form("form_editar_assinatura", border=False):

                    usuario_editado = st.selectbox(
                        "Usuário",
                        list(opcoes_usuarios.keys()),
                        index=list(opcoes_usuarios.values()).index(
                            assinatura["id_usuario"]
                        )
                    )

                    inicio_editado = st.date_input(
                        "Data de início",
                        value=inicio_atual,
                        key="edicao_data_inicio",
                        format="DD/MM/YYYY"
                    )

                    salvar = st.form_submit_button(
                        "Salvar alterações",
                        use_container_width=True,
                        type="primary"
                    )

                    if salvar:

                        try:
                            atualizar_assinatura(
                                id_assinatura=id_selecionado,
                                id_usuario=opcoes_usuarios[usuario_editado],
                                id_plano=id_plano_editado,
                                data_inicio=inicio_editado,
                                data_termino=assinatura["data_termino"],
                                status=assinatura["status"],
                                valor=valor_editado
                            )

                            st.success("Assinatura atualizada com sucesso!")
                            st.rerun()

                        except ErroAplicacao as e:
                            st.error(str(e))

                        except Exception as e:
                            st.error(f"Erro ao atualizar assinatura: {e}")

        else:
            st.info("Não existem assinaturas para editar.")

    # ========================================================
    # ENCERRAMENTO
    # ========================================================
    with aba_encerrar:

        assinaturas_ativas = [
            a for a in assinaturas
            if a["status"] == "ativa"
        ]

        if assinaturas_ativas:

            opcoes_ativas = {
                f'ID {a["id_assinatura"]} - {a["usuario"]} '
                f'({a["plano"].title()})': a["id_assinatura"]
                for a in assinaturas_ativas
            }

            with st.container(border=True):

                st.markdown("**Encerrar assinatura**")

                assinatura_ativa = st.selectbox(
                    "Selecione a assinatura ativa",
                    list(opcoes_ativas.keys()),
                    key="encerrar_assinatura"
                )

                id_ativa = opcoes_ativas[assinatura_ativa]

                with st.form("form_encerrar_assinatura", border=False):

                    col1, col2 = st.columns(2, gap="medium")

                    with col1:
                        novo_status = st.selectbox(
                            "Motivo do encerramento",
                            ["Cancelada", "Expirada"]
                        )

                    with col2:
                        data_encerramento = st.date_input(
                            "Data de término",
                            value=date.today(),
                            key="data_encerramento",
                            format="DD/MM/YYYY"
                        )

                    encerrar = st.form_submit_button(
                        "Encerrar assinatura",
                        use_container_width=True,
                        type="primary"
                    )

                    if encerrar:

                        try:
                            encerrar_assinatura(
                                id_assinatura=id_ativa,
                                data_termino=data_encerramento,
                                status=STATUS[novo_status]
                            )

                            st.success("Assinatura encerrada com sucesso!")
                            st.rerun()

                        except ErroAplicacao as e:
                            st.error(str(e))

                        except Exception as e:
                            st.error(f"Erro ao encerrar assinatura: {e}")

        else:
            st.info("Não existem assinaturas ativas para encerrar.")

    # ========================================================
    # EXCLUSÃO
    # ========================================================
    with aba_exclusao:

        if assinaturas:

            with st.container(border=True):

                st.markdown("**Excluir assinatura**")

                st.warning(
                    "Esta ação não pode ser desfeita.",
                    icon="⚠️"
                )

                assinatura_excluir = st.selectbox(
                    "Selecione a assinatura para excluir",
                    list(opcoes_assinaturas.keys()),
                    key="excluir_assinatura"
                )

                id_excluir = opcoes_assinaturas[assinatura_excluir]

                confirmar = st.checkbox(
                    "Confirmo que desejo excluir esta assinatura.",
                    key="confirmar_exclusao_assinatura"
                )

                if st.button(
                    "Excluir assinatura",
                    use_container_width=True,
                    type="primary"
                ):

                    if confirmar:
                        try:
                            excluir_assinatura(id_excluir)

                            st.success("Assinatura excluída com sucesso!")
                            st.rerun()

                        except ErroAplicacao as e:
                            st.error(str(e))

                        except Exception as e:
                            st.error(f"Erro ao excluir assinatura: {e}")

                    else:
                        st.warning(
                            "Marque a confirmação antes de excluir."
                        )

        else:
            st.info("Não existem assinaturas para excluir.")