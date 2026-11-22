import streamlit as st
import pandas as pd
import altair as alt

from services.historico_service import (
    listar_historico,
    registrar_reproducao,
    excluir_reproducao
)

from services.usuario_service import listar_usuarios
from services.conteudo_service import listar_catalogo
from services.episodio_service import listar_episodios

from database.erros import ErroAplicacao


# Cores (iguais às do app.py)
COR_PRIMARIA = "#E50914"
COR_BORDA = "#2A3042"
COR_TEXTO = "#F5F6F8"
COR_TEXTO_SUAVE = "#9AA3B5"



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


def mostrar_historico():

    cabecalho_pagina(
        "ACOMPANHAMENTO",
        "Histórico de reproduções",
        "Consulte, registre e acompanhe as reproduções "
        "realizadas pelos usuários."
    )

    
    # Consulta ao banco de dados
    
    try:
        historico = listar_historico()
        usuarios = listar_usuarios()
        catalogo = listar_catalogo()
        episodios = listar_episodios()

    except ErroAplicacao as e:
        st.error(str(e))
        return

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return

    
    # Indicadores
    
    total = len(historico)

    tempo_total = sum(
        float(h["progresso_minutos"] or 0)
        for h in historico
    )

    conteudos_unicos = len({
        h["conteudo"] for h in historico
    })

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        cartao_indicador(
            "▶", "Reproduções",
            formatar_numero(total),
            "Total de reproduções registradas"
        )

    with col2:
        cartao_indicador(
            "⏱", "Tempo assistido",
            f"{tempo_total:g} min",
            f"≈ {tempo_total / 60:.1f} horas no total".replace(".", ",")
        )

    with col3:
        cartao_indicador(
            "", "Conteúdos",
            formatar_numero(conteudos_unicos),
            "Títulos diferentes reproduzidos"
        )

    st.write("")
    st.write("")

    
    # Seções
    
    aba_lista, aba_ranking, aba_registro, aba_exclusao = st.tabs([
        "Reproduções",
        "Ranking",
        "Registrar",
        "Excluir"
    ])

    
    # LISTAGEM E FILTROS
    
    with aba_lista:

        titulo_secao(
            "Reproduções registradas",
            "Pesquise por usuário, conteúdo ou episódio."
        )

        with st.container(border=True):

            col1, col2 = st.columns([3, 1], gap="medium")

            with col1:
                pesquisa = st.text_input(
                    "Pesquisar",
                    placeholder="🔍  Usuário, conteúdo ou episódio..."
                )

            with col2:
                filtro_tipo = st.selectbox(
                    "Tipo de conteúdo",
                    ["Todos", "Filme", "Série"]
                )

            historico_filtrado = historico.copy()

            if pesquisa.strip():

                termo = pesquisa.lower()

                historico_filtrado = [
                    h for h in historico_filtrado
                    if termo in h["usuario"].lower()
                    or termo in h["conteudo"].lower()
                    or termo in (h["titulo_episodio"] or "").lower()
                ]

            if filtro_tipo != "Todos":

                tipo_db = {
                    "Filme": "filme",
                    "Série": "serie"
                }[filtro_tipo]

                historico_filtrado = [
                    h for h in historico_filtrado
                    if h["tipo"] == tipo_db
                ]

            if historico_filtrado:

                df = pd.DataFrame(historico_filtrado)

                df["data_hora"] = pd.to_datetime(
                    df["data_hora"]
                ).dt.strftime("%d/%m/%Y %H:%M")

                def identificar_episodio(linha):
                    if linha["tipo"] == "filme":
                        return "-"

                    if pd.isna(linha["episodio"]):
                        return "Episódio não identificado"

                    return (
                        f'T{int(linha["temporada"])} '
                        f'E{int(linha["episodio"])} - '
                        f'{linha["titulo_episodio"]}'
                    )

                df["episodio_exibicao"] = df.apply(
                    identificar_episodio,
                    axis=1
                )

                df["tipo"] = df["tipo"].map({
                    "filme": "🍿 Filme",
                    "serie": "📺 Série"
                })

                df = df[[
                    "id_reproducao",
                    "usuario",
                    "conteudo",
                    "tipo",
                    "episodio_exibicao",
                    "data_hora",
                    "progresso_minutos"
                ]]

                df = df.rename(columns={
                    "id_reproducao": "ID",
                    "usuario": "Usuário",
                    "conteudo": "Conteúdo",
                    "tipo": "Tipo",
                    "episodio_exibicao": "Episódio",
                    "data_hora": "Data e horário",
                    "progresso_minutos": "Minutos assistidos"
                })

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
                st.info("Nenhuma reprodução encontrada.")

    
    # RANKING
    
    with aba_ranking:

        titulo_secao(
            "Conteúdos mais reproduzidos",
            "Os 10 conteúdos com maior número de reproduções."
        )

        if historico:

            df_grafico = pd.DataFrame(historico)

            reproducoes = (
                df_grafico.groupby("conteudo")
                .size()
                .reset_index(name="Reproduções")
                .rename(columns={"conteudo": "Conteúdo"})
                .sort_values("Reproduções", ascending=False)
                .head(10)
            )

            col_grafico, col_lista = st.columns([3, 2], gap="large")

            with col_grafico:

                with st.container(border=True):

                    grafico = (
                        alt.Chart(reproducoes)
                        .mark_bar(
                            cornerRadiusTopRight=8,
                            cornerRadiusBottomRight=8,
                            color=COR_PRIMARIA,
                            size=22
                        )
                        .encode(
                            x=alt.X(
                                "Reproduções:Q",
                                title=None,
                                axis=alt.Axis(
                                    grid=True,
                                    gridColor=COR_BORDA,
                                    labelColor=COR_TEXTO_SUAVE,
                                    domain=False,
                                    tickMinStep=1
                                )
                            ),
                            y=alt.Y(
                                "Conteúdo:N",
                                sort="-x",
                                title=None,
                                axis=alt.Axis(
                                    labelColor=COR_TEXTO,
                                    labelLimit=220,
                                    domain=False,
                                    ticks=False
                                )
                            ),
                            tooltip=["Conteúdo", "Reproduções"]
                        )
                        .properties(height=max(260, 48 * len(reproducoes)))
                        .configure(background="transparent")
                        .configure_view(strokeWidth=0)
                    )

                    st.altair_chart(grafico, use_container_width=True)

            with col_lista:

                with st.container(border=True):

                    st.markdown("**🏆 Top conteúdos**")

                    for posicao, linha in enumerate(
                        reproducoes.itertuples(index=False), start=1
                    ):
                        st.markdown(f"""
                        <div class="rank-item">
                            <div class="rank-pos">{posicao}</div>
                            <div class="rank-nome">{linha[0]}</div>
                            <div class="rank-valor">
                                {formatar_numero(linha[1])} ▶
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        else:
            st.info(
                "Ainda não existem reproduções para visualizar."
            )

    
    # CADASTRO DE REPRODUÇÃO
    
    with aba_registro:

        if not usuarios:
            st.warning("Cadastre pelo menos um usuário antes de registrar reproduções.")

        elif not catalogo:
            st.warning("Cadastre pelo menos um filme ou série no catálogo.")

        else:

            usuarios_por_id = {
                u["id_usuario"]: u for u in usuarios
            }

            conteudos_por_id = {
                c["id_conteudo"]: c for c in catalogo
            }

            episodios_disponiveis = []

            with st.container(border=True):

                st.markdown("**Registrar reprodução**")

                col1, col2 = st.columns(2, gap="medium")

                with col1:
                    id_usuario = st.selectbox(
                        "Usuário",
                        list(usuarios_por_id.keys()),
                        format_func=lambda id: (
                            f'{usuarios_por_id[id]["nome"]} '
                            f'(ID: {id})'
                        ),
                        key="historico_usuario"
                    )

                with col2:
                    id_conteudo = st.selectbox(
                        "Conteúdo",
                        list(conteudos_por_id.keys()),
                        format_func=lambda id: (
                            f'{conteudos_por_id[id]["titulo"]} '
                            f'({"Filme" if conteudos_por_id[id]["tipo"] == "filme" else "Série"})'
                        ),
                        key="historico_conteudo"
                    )

                conteudo = conteudos_por_id[id_conteudo]

                id_episodio = None
                duracao = conteudo["duracao_minutos"]

                if conteudo["tipo"] == "serie":

                    episodios_disponiveis = [
                        e for e in episodios
                        if e["id_serie"] == id_conteudo
                    ]

                    if episodios_disponiveis:

                        episodios_por_id = {
                            e["id_episodio"]: e
                            for e in episodios_disponiveis
                        }

                        id_episodio = st.selectbox(
                            "Episódio",
                            list(episodios_por_id.keys()),
                            format_func=lambda id: (
                                f'Temporada {episodios_por_id[id]["temporada"]} - '
                                f'Episódio {episodios_por_id[id]["episodio"]}: '
                                f'{episodios_por_id[id]["titulo"]}'
                            ),
                            key=f"historico_episodio_{id_conteudo}"
                        )

                        duracao = episodios_por_id[id_episodio]["duracao_minutos"]

                    else:
                        st.warning(
                            "Esta série ainda não possui episódios cadastrados."
                        )

                progresso = None

                if duracao is not None:
                    progresso = st.number_input(
                        "Minutos assistidos",
                        min_value=0.0,
                        max_value=float(duracao),
                        value=0.0,
                        step=1.0,
                        key="historico_progresso",
                        help=f"Duração total: {duracao} minutos."
                    )
                else:
                    st.info(
                        "Não foi possível identificar a duração. "
                        "Verifique o cadastro do conteúdo ou do episódio."
                    )

                pode_registrar = (
                    conteudo["tipo"] == "filme"
                    or bool(episodios_disponiveis)
                )

                if st.button(
                    "Registrar reprodução",
                    use_container_width=True,
                    disabled=not pode_registrar,
                    type="primary"
                ):

                    try:
                        registrar_reproducao(
                            id_usuario=id_usuario,
                            id_conteudo=id_conteudo,
                            id_episodio=id_episodio,
                            progresso_minutos=progresso
                        )

                        st.success("Reprodução registrada com sucesso!")
                        st.rerun()

                    except ErroAplicacao as e:
                        st.error(str(e))

                    except Exception as e:
                        st.error(f"Erro ao registrar reprodução: {e}")

    
    # EXCLUSÃO
    
    with aba_exclusao:

        if historico:

            opcoes = {
                (
                    f'ID {h["id_reproducao"]} - '
                    f'{h["usuario"]} - {h["conteudo"]}'
                    + (
                        f' - {h["titulo_episodio"]}'
                        if h["titulo_episodio"]
                        else ""
                    )
                ): h["id_reproducao"]
                for h in historico
            }

            with st.container(border=True):

                st.markdown("**Excluir reprodução**")

                st.warning(
                    "Esta ação não pode ser desfeita.",
                    icon="⚠️"
                )

                reproducao_selecionada = st.selectbox(
                    "Selecione a reprodução",
                    list(opcoes.keys()),
                    key="excluir_historico"
                )

                id_excluir = opcoes[reproducao_selecionada]

                confirmar = st.checkbox(
                    "Confirmo que desejo excluir esta reprodução.",
                    key="confirmar_exclusao_historico"
                )

                if st.button(
                    "Excluir reprodução",
                    use_container_width=True,
                    type="primary"
                ):

                    if confirmar:

                        try:
                            excluir_reproducao(id_excluir)

                            st.success(
                                "Reprodução excluída com sucesso!"
                            )

                            st.rerun()

                        except ErroAplicacao as e:
                            st.error(str(e))

                        except Exception as e:
                            st.error(
                                f"Erro ao excluir reprodução: {e}"
                            )

                    else:
                        st.warning(
                            "Marque a confirmação antes de excluir."
                        )

        else:
            st.info(
                "Não existem reproduções para excluir."
            )