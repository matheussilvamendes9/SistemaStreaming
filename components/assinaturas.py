
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from services.assinatura_service import (
    listar_assinaturas,
    criar_assinatura,
    atualizar_assinatura,
    excluir_assinatura
)

from services.usuario_service import listar_usuarios
from database.erros import ErroAplicacao


# Opções e valores dos planos
PLANOS = {
    "Básico": ("basico", 19.90),
    "Padrão": ("padrao", 29.90),
    "Premium": ("premium", 39.90)
}

STATUS = {
    "Ativa": "ativa",
    "Cancelada": "cancelada",
    "Expirada": "expirada"
}


def mostrar_assinaturas():

    st.title("Gerenciamento de Assinaturas")
    st.write("Gerencie os planos e assinaturas dos usuários.")

    # Carregamento dos dados
    try:
        assinaturas = listar_assinaturas()
        usuarios = listar_usuarios()

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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total de assinaturas", total)
    col2.metric("Ativas", ativas)
    col3.metric("Canceladas", canceladas)
    col4.metric("Expiradas", expiradas)

    st.divider()

    # Consulta e filtros
    st.subheader("Assinaturas cadastradas")

    col1, col2 = st.columns(2)

    with col1:
        pesquisa = st.text_input(
            "Pesquisar usuário",
            placeholder="Digite o nome do usuário..."
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
            "plano": "Plano",
            "valor": "Valor",
            "data_inicio": "Data de início",
            "data_termino": "Data de término",
            "status": "Status"
        })

        df["Plano"] = df["Plano"].map({
            "basico": "Básico",
            "padrao": "Padrão",
            "premium": "Premium"
        })

        df["Status"] = df["Status"].map({
            "ativa": "Ativa",
            "cancelada": "Cancelada",
            "expirada": "Expirada"
        })

        df["Valor"] = df["Valor"].apply(
            lambda v: f"R$ {float(v):.2f}".replace(".", ",")
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Nenhuma assinatura encontrada.")

    st.divider()

    # Verificação de usuários disponíveis
    if not usuarios:
        st.warning(
            "Não existem usuários cadastrados. "
            "Cadastre um usuário antes de criar uma assinatura."
        )
        return

    opcoes_usuarios = {
        f'{u["nome"]} (ID: {u["id_usuario"]})': u["id_usuario"]
        for u in usuarios
    }

    # Cadastro
    st.subheader("Cadastrar nova assinatura")

    with st.form("form_cadastro_assinatura"):

        usuario_selecionado = st.selectbox(
            "Usuário",
            list(opcoes_usuarios.keys())
        )

        plano_selecionado = st.selectbox(
            "Plano",
            list(PLANOS.keys())
        )

        valor_plano = PLANOS[plano_selecionado][1]

        st.write(f"Valor do plano: R$ {valor_plano:.2f}")

        data_inicio = st.date_input(
            "Data de início",
            value=date.today(),
            key="cadastro_data_inicio"
        )

        possui_termino = st.checkbox(
            "Definir data de término",
            value=True,
            key="cadastro_possui_termino"
        )

        data_termino = None

        if possui_termino:
            data_termino = st.date_input(
                "Data de término",
                value=date.today() + timedelta(days=30),
                key="cadastro_data_termino"
            )

        status_selecionado = st.selectbox(
            "Status",
            list(STATUS.keys()),
            key="cadastro_status"
        )

        cadastrar = st.form_submit_button(
            "Cadastrar assinatura",
            use_container_width=True
        )

        if cadastrar:

            if data_termino and data_termino < data_inicio:
                st.error(
                    "A data de término não pode ser anterior "
                    "à data de início."
                )

            else:
                try:
                    criar_assinatura(
                        id_usuario=opcoes_usuarios[usuario_selecionado],
                        plano=PLANOS[plano_selecionado][0],
                        valor=valor_plano,
                        data_inicio=data_inicio,
                        data_termino=data_termino,
                        status=STATUS[status_selecionado]
                    )

                    st.success("Assinatura cadastrada com sucesso!")
                    st.rerun()

                except ErroAplicacao as e:
                    st.error(str(e))

                except Exception as e:
                    st.error(f"Erro ao cadastrar assinatura: {e}")

    st.divider()

    # Edição
    st.subheader("Editar assinatura")

    if assinaturas:

        opcoes_assinaturas = {
            f'ID {a["id_assinatura"]} - {a["usuario"]} '
            f'({a["plano"]})': a["id_assinatura"]
            for a in assinaturas
        }

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

        plano_atual = assinatura["plano"]

        nome_plano_atual = next(
            nome for nome, dados in PLANOS.items()
            if dados[0] == plano_atual
        )

        status_atual = assinatura["status"]

        nome_status_atual = next(
            nome for nome, valor in STATUS.items()
            if valor == status_atual
        )

        data_inicio_atual = assinatura["data_inicio"]
        data_termino_atual = assinatura["data_termino"]

        with st.form("form_editar_assinatura"):

            usuario_editado = st.selectbox(
                "Usuário",
                list(opcoes_usuarios.keys()),
                index=list(opcoes_usuarios.values()).index(
                    assinatura["id_usuario"]
                )
            )

            plano_editado = st.selectbox(
                "Plano",
                list(PLANOS.keys()),
                index=list(PLANOS.keys()).index(nome_plano_atual)
            )

            novo_valor = PLANOS[plano_editado][1]

            st.write(f"Valor do plano: R$ {novo_valor:.2f}")

            inicio_editado = st.date_input(
                "Data de início",
                value=data_inicio_atual,
                key="edicao_data_inicio"
            )

            possui_termino_editado = st.checkbox(
                "Definir data de término",
                value=data_termino_atual is not None,
                key="edicao_possui_termino"
            )

            fim_editado = None

            if possui_termino_editado:
                fim_editado = st.date_input(
                    "Data de término",
                    value=data_termino_atual or (
                        inicio_editado + timedelta(days=30)
                    ),
                    key="edicao_data_termino"
                )

            status_editado = st.selectbox(
                "Status",
                list(STATUS.keys()),
                index=list(STATUS.keys()).index(nome_status_atual)
            )

            salvar = st.form_submit_button(
                "Salvar alterações",
                use_container_width=True
            )

            if salvar:

                if fim_editado and fim_editado < inicio_editado:
                    st.error(
                        "A data de término não pode ser anterior "
                        "à data de início."
                    )

                else:
                    try:
                        atualizar_assinatura(
                            id_assinatura=id_selecionado,
                            id_usuario=opcoes_usuarios[usuario_editado],
                            plano=PLANOS[plano_editado][0],
                            valor=novo_valor,
                            data_inicio=inicio_editado,
                            data_termino=fim_editado,
                            status=STATUS[status_editado]
                        )

                        st.success("Assinatura atualizada com sucesso!")
                        st.rerun()

                    except ErroAplicacao as e:
                        st.error(str(e))

                    except Exception as e:
                        st.error(f"Erro ao atualizar assinatura: {e}")

    else:
        st.info("Não existem assinaturas para editar.")

    st.divider()

    # Exclusão
    st.subheader("Excluir assinatura")

    if assinaturas:

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
            use_container_width=True
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
