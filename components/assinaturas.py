import streamlit as st
import pandas as pd
from datetime import date, timedelta


def mostrar_assinaturas():

    # Inicializa os dados fictícios
    if "assinaturas" not in st.session_state:
        st.session_state.assinaturas = [
            {
                "id": 1,
                "usuario": "Ana Souza",
                "plano": "Premium",
                "data_inicio": date(2026, 10, 1),
                "data_fim": date(2026, 11, 1),
                "status": "Ativa",
                "valor": 39.90
            },
            {
                "id": 2,
                "usuario": "Carlos Mendes",
                "plano": "Básico",
                "data_inicio": date(2026, 9, 15),
                "data_fim": date(2026, 10, 15),
                "status": "Expirada",
                "valor": 19.90
            },
            {
                "id": 3,
                "usuario": "Mariana Lima",
                "plano": "Padrão",
                "data_inicio": date(2026, 10, 10),
                "data_fim": date(2026, 11, 10),
                "status": "Ativa",
                "valor": 29.90
            }
        ]

    # Restante da implementação virá abaixo
        st.title("Gerenciamento de Assinaturas")
    st.write("Gerencie os planos e assinaturas dos usuários.")

    assinaturas = st.session_state.assinaturas

    # Indicadores
    total = len(assinaturas)
    ativas = sum(1 for a in assinaturas if a["status"] == "Ativa")
    canceladas = sum(1 for a in assinaturas if a["status"] == "Cancelada")
    expiradas = sum(1 for a in assinaturas if a["status"] == "Expirada")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total de assinaturas", total)
    col2.metric("Ativas", ativas)
    col3.metric("Canceladas", canceladas)
    col4.metric("Expiradas", expiradas)

    st.divider()

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

    assinaturas_filtradas = assinaturas.copy()

    if pesquisa:
        assinaturas_filtradas = [
            a for a in assinaturas_filtradas
            if pesquisa.lower() in a["usuario"].lower()
        ]

    if filtro_status != "Todos":
        assinaturas_filtradas = [
            a for a in assinaturas_filtradas
            if a["status"] == filtro_status
        ]

    if assinaturas_filtradas:
        df = pd.DataFrame(assinaturas_filtradas)

        df["valor"] = df["valor"].apply(
            lambda valor: f"R$ {valor:.2f}"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma assinatura encontrada.")
    st.divider()
    st.subheader("Cadastrar nova assinatura")

    with st.form("form_cadastro_assinatura"):

        usuario = st.selectbox(
            "Usuário",
            ["Ana Souza", "Carlos Mendes", "Mariana Lima"]
        )

        plano = st.selectbox(
            "Plano",
            ["Básico", "Padrão", "Premium"]
        )

        data_inicio = st.date_input(
            "Data de início",
            value=date.today()
        )

        data_fim = st.date_input(
            "Data de término",
            value=date.today() + timedelta(days=30)
        )

        status = st.selectbox(
            "Status",
            ["Ativa", "Cancelada", "Expirada"]
        )

        precos = {
            "Básico": 19.90,
            "Padrão": 29.90,
            "Premium": 39.90
        }

        st.write(f"Valor do plano: R$ {precos[plano]:.2f}")

        cadastrar = st.form_submit_button(
            "Cadastrar assinatura"
        )

        if cadastrar:

            if data_fim <= data_inicio:
                st.error("A data de término deve ser posterior à data de início.")

            else:
                novo_id = max(
                    [a["id"] for a in assinaturas],
                    default=0
                ) + 1

                nova_assinatura = {
                    "id": novo_id,
                    "usuario": usuario,
                    "plano": plano,
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "status": status,
                    "valor": precos[plano]
                }

                st.session_state.assinaturas.append(
                    nova_assinatura
                )

                st.success("Assinatura cadastrada com sucesso!")
                st.rerun()
    st.divider()
    st.subheader("Editar assinatura")

    if assinaturas:

        opcoes = {
            f"ID {a['id']} - {a['usuario']} ({a['plano']})": a["id"]
            for a in assinaturas
        }

        assinatura_selecionada = st.selectbox(
            "Selecione a assinatura",
            list(opcoes.keys()),
            key="editar_assinatura"
        )

        id_selecionado = opcoes[assinatura_selecionada]

        assinatura = next(
            a for a in assinaturas
            if a["id"] == id_selecionado
        )

        with st.form("form_editar_assinatura"):

            usuario_editado = st.selectbox(
                "Usuário",
                ["Ana Souza", "Carlos Mendes", "Mariana Lima"],
                index=["Ana Souza", "Carlos Mendes", "Mariana Lima"].index(
                    assinatura["usuario"]
                )
            )

            plano_editado = st.selectbox(
                "Plano",
                ["Básico", "Padrão", "Premium"],
                index=["Básico", "Padrão", "Premium"].index(
                    assinatura["plano"]
                )
            )

            inicio_editado = st.date_input(
                "Data de início",
                value=assinatura["data_inicio"]
            )

            fim_editado = st.date_input(
                "Data de término",
                value=assinatura["data_fim"]
            )

            status_editado = st.selectbox(
                "Status",
                ["Ativa", "Cancelada", "Expirada"],
                index=["Ativa", "Cancelada", "Expirada"].index(
                    assinatura["status"]
                )
            )

            salvar = st.form_submit_button("Salvar alterações")

            if salvar:

                if fim_editado <= inicio_editado:
                    st.error("A data de término deve ser posterior à data de início.")

                else:
                    precos = {
                        "Básico": 19.90,
                        "Padrão": 29.90,
                        "Premium": 39.90
                    }

                    for a in st.session_state.assinaturas:
                        if a["id"] == id_selecionado:
                            a["usuario"] = usuario_editado
                            a["plano"] = plano_editado
                            a["data_inicio"] = inicio_editado
                            a["data_fim"] = fim_editado
                            a["status"] = status_editado
                            a["valor"] = precos[plano_editado]

                    st.success("Assinatura atualizada!")
                    st.rerun()
    st.divider()
    st.subheader("Excluir assinatura")

    if assinaturas:

        opcoes_exclusao = {
            f"ID {a['id']} - {a['usuario']} ({a['plano']})": a["id"]
            for a in assinaturas
        }

        assinatura_excluir = st.selectbox(
            "Selecione a assinatura para excluir",
            list(opcoes_exclusao.keys()),
            key="excluir_assinatura"
        )

        id_excluir = opcoes_exclusao[assinatura_excluir]

        confirmar = st.checkbox(
            "Confirmo que desejo excluir esta assinatura."
        )

        if st.button("Excluir assinatura", type="primary"):

            if confirmar:

                st.session_state.assinaturas = [
                    a for a in st.session_state.assinaturas
                    if a["id"] != id_excluir
                ]

                st.success("Assinatura excluída!")
                st.rerun()

            else:
                st.warning("Marque a confirmação antes de excluir.")