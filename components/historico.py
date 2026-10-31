import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def mostrar_historico():

    # Inicializa os dados fictícios
    if "historico" not in st.session_state:
        agora = datetime.now()

        st.session_state.historico = [
            {
                "id": 1,
                "usuario": "Ana Souza",
                "conteudo": "Interestelar",
                "tipo": "Filme",
                "data": agora - timedelta(days=1),
                "duracao": 120,
                "status": "Concluída"
            },
            {
                "id": 2,
                "usuario": "Carlos Mendes",
                "conteudo": "Breaking Bad",
                "tipo": "Série",
                "data": agora - timedelta(days=2),
                "duracao": 35,
                "status": "Interrompida"
            },
            {
                "id": 3,
                "usuario": "Mariana Lima",
                "conteudo": "A Origem",
                "tipo": "Filme",
                "data": agora - timedelta(days=3),
                "duracao": 90,
                "status": "Concluída"
            },
            {
                "id": 4,
                "usuario": "Ana Souza",
                "conteudo": "Dark",
                "tipo": "Série",
                "data": agora - timedelta(hours=5),
                "duracao": 25,
                "status": "Em andamento"
            },
            {
                "id": 5,
                "usuario": "Carlos Mendes",
                "conteudo": "Interestelar",
                "tipo": "Filme",
                "data": agora - timedelta(hours=2),
                "duracao": 60,
                "status": "Interrompida"
            }
        ]

    # Continuaremos a implementação abaixo
    st.title("Histórico de Reproduções")
    st.write("Consulte e acompanhe as reproduções realizadas pelos usuários.")

    historico = st.session_state.historico

    # Indicadores
    total = len(historico)

    concluidas = sum(
        1 for h in historico
        if h["status"] == "Concluída"
    )

    em_andamento = sum(
        1 for h in historico
        if h["status"] == "Em andamento"
    )

    tempo_total = sum(
        h["duracao"] for h in historico
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total de reproduções", total)
    col2.metric("Concluídas", concluidas)
    col3.metric("Em andamento", em_andamento)
    col4.metric("Tempo assistido", f"{tempo_total} min")

    st.divider()
    st.subheader("Reproduções registradas")

    col1, col2, col3 = st.columns(3)

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

    with col3:
        filtro_status = st.selectbox(
            "Status",
            ["Todos", "Concluída", "Em andamento", "Interrompida"]
        )

    historico_filtrado = historico.copy()

    # Pesquisa por usuário ou conteúdo
    if pesquisa:
        historico_filtrado = [
            h for h in historico_filtrado
            if pesquisa.lower() in h["usuario"].lower()
            or pesquisa.lower() in h["conteudo"].lower()
        ]

    # Filtro por tipo
    if filtro_tipo != "Todos":
        historico_filtrado = [
            h for h in historico_filtrado
            if h["tipo"] == filtro_tipo
        ]

    # Filtro por status
    if filtro_status != "Todos":
        historico_filtrado = [
            h for h in historico_filtrado
            if h["status"] == filtro_status
        ]

    if historico_filtrado:

        df = pd.DataFrame(historico_filtrado)

        df["data"] = df["data"].dt.strftime("%d/%m/%Y %H:%M")

        df = df.rename(columns={
            "id": "ID",
            "usuario": "Usuário",
            "conteudo": "Conteúdo",
            "tipo": "Tipo",
            "data": "Data e horário",
            "duracao": "Minutos assistidos",
            "status": "Status"
        })

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Nenhuma reprodução encontrada.")

    st.divider()
    st.subheader("Conteúdos mais reproduzidos")

    if historico:

        df_grafico = pd.DataFrame(historico)

        reproducoes = (
            df_grafico.groupby("conteudo")
            .size()
            .reset_index(name="Reproduções")
        )

        reproducoes = reproducoes.set_index("conteudo")

        st.bar_chart(reproducoes)

    else:
        st.info("Ainda não existem reproduções para visualizar.")

    st.divider()
    st.subheader("Adicionar reprodução de teste")

    with st.form("form_cadastro_historico"):

        usuario = st.selectbox(
            "Usuário",
            ["Ana Souza", "Carlos Mendes", "Mariana Lima"]
        )

        conteudo = st.selectbox(
            "Conteúdo",
            ["Interestelar", "Breaking Bad", "A Origem", "Dark"]
        )

        tipo = "Filme" if conteudo in ["Interestelar", "A Origem"] else "Série"

        data_reproducao = st.date_input(
            "Data da reprodução",
            value=datetime.today().date()
        )

        horario = st.time_input(
            "Horário da reprodução",
            value=datetime.now().time().replace(second=0, microsecond=0)
        )

        duracao = st.number_input(
            "Minutos assistidos",
            min_value=1,
            max_value=1000,
            value=30
        )

        status = st.selectbox(
            "Status",
            ["Em andamento", "Concluída", "Interrompida"]
        )

        cadastrar = st.form_submit_button(
            "Adicionar reprodução"
        )

        if cadastrar:

            nova_data = datetime.combine(
                data_reproducao,
                horario
            )

            if nova_data > datetime.now():
                st.error("A data da reprodução não pode estar no futuro.")

            else:

                novo_id = max(
                    [h["id"] for h in historico],
                    default=0
                ) + 1

                nova_reproducao = {
                    "id": novo_id,
                    "usuario": usuario,
                    "conteudo": conteudo,
                    "tipo": tipo,
                    "data": nova_data,
                    "duracao": int(duracao),
                    "status": status
                }

                st.session_state.historico.append(
                    nova_reproducao
                )

                st.success("Reprodução adicionada com sucesso!")
                st.rerun()

    st.divider()
    st.subheader("Excluir reprodução")

    if historico:

        opcoes = {
            f"ID {h['id']} - {h['usuario']} - {h['conteudo']}": h["id"]
            for h in historico
        }

        reproducao_selecionada = st.selectbox(
            "Selecione a reprodução",
            list(opcoes.keys()),
            key="excluir_historico"
        )

        id_excluir = opcoes[reproducao_selecionada]

        confirmar = st.checkbox(
            "Confirmo que desejo excluir esta reprodução."
        )

        if st.button("Excluir reprodução", type="primary"):

            if confirmar:

                st.session_state.historico = [
                    h for h in st.session_state.historico
                    if h["id"] != id_excluir
                ]

                st.success("Reprodução excluída com sucesso!")
                st.rerun()

            else:
                st.warning("Marque a confirmação antes de excluir.")