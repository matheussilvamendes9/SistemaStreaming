
import streamlit as st
import pandas as pd
import altair as alt

from services.analise_service import (
    obter_indicadores_imdb,
    obter_producao_por_ano,
    obter_duracao_media_por_ano,
    obter_top_filmes_por_genero,
    obter_resumo_por_tipo,
    obter_series_sem_ano_termino,
    obter_distribuicao_notas
)



# CONFIGURAÇÕES VISUAIS


COR_PRIMARIA = "#E50914"
COR_SECUNDARIA = "#64748B"



# FUNÇÕES AUXILIARES


def formatar_numero(valor):
    if valor is None:
        return "0"

    return f"{int(valor):,}".replace(",", ".")


def formatar_nota(valor):
    if valor is None:
        return "N/A"

    return f"{float(valor):.2f}".replace(".", ",")



# CACHE DAS CONSULTAS


@st.cache_data(ttl=3600)
def carregar_indicadores():
    return obter_indicadores_imdb()


@st.cache_data(ttl=3600)
def carregar_resumo_por_tipo():
    return obter_resumo_por_tipo()


@st.cache_data(ttl=3600)
def carregar_series_sem_ano_termino():
    return obter_series_sem_ano_termino()


@st.cache_data(ttl=3600)
def carregar_distribuicao_notas(tipo, votos_minimos):
    return obter_distribuicao_notas(tipo, votos_minimos)


# PÁGINA DE ANÁLISE


def mostrar_analise():

    st.title("Análise de Dados")
    st.markdown(
        "Explore indicadores e tendências do mercado audiovisual "
        "a partir dos dados disponibilizados pelo IMDb."
    )

    st.divider()

    try:

        
        # 
        # 1. VISÃO GERAL
        # 

        st.subheader("Visão geral do catálogo IMDb")

        indicadores = carregar_indicadores()
        resumo_tipos = carregar_resumo_por_tipo()
        series_sem_termino = carregar_series_sem_ano_termino()

        # Organiza os resultados por tipo
        tipos = {
            item["tipo"]: item
            for item in resumo_tipos
        }

        total_titulos = sum(
            item["total_titulos"]
            for item in resumo_tipos
        )

        total_avaliados = sum(
            item["titulos_avaliados"]
            for item in resumo_tipos
        )

        total_votos = sum(
            item["total_votos"]
            for item in resumo_tipos
        )

        # Primeira linha de indicadores
        col1, col2, col3, col4 = st.columns(4, gap="medium")

        with col1:
            st.metric(
                "🎞️ Total de títulos",
                formatar_numero(total_titulos)
            )

        with col2:
            st.metric(
                "🎬 Filmes",
                formatar_numero(
                    tipos.get("movie", {}).get("total_titulos", 0)
                )
            )

        with col3:
            st.metric(
                "📺 Séries",
                formatar_numero(
                    tipos.get("tvSeries", {}).get("total_titulos", 0)
                )
            )

        with col4:
            st.metric(
                "⭐ Títulos avaliados",
                formatar_numero(total_avaliados)
            )

        # Segunda linha de indicadores
        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            st.metric(
                "📊 Nota média IMDb",
                formatar_nota(indicadores["nota_media"])
            )

        with col2:
            st.metric(
                "🗳️ Total de votos",
                formatar_numero(total_votos)
            )

        with col3:
            st.metric(
                "⏳ Séries sem ano de término",
                formatar_numero(series_sem_termino)
            )

        st.caption(
            "A quantidade de séries sem ano de término não significa "
            "necessariamente que elas ainda estejam em exibição."
        )

        st.divider()

        # 
        # 2. COMPARAÇÃO ENTRE TIPOS DE PRODUÇÃO
        # 

        st.subheader("Panorama por tipo de produção")

        if resumo_tipos:

            df_tipos = pd.DataFrame(resumo_tipos)

            nomes_tipos = {
                "movie": "Filmes",
                "tvSeries": "Séries",
                "tvEpisode": "Episódios",
                "short": "Curtas",
                "tvMiniSeries": "Minisséries",
                "tvMovie": "Telefilmes",
                "videoGame": "Jogos",
                "video": "Vídeos"
            }

            df_tipos["tipo"] = df_tipos["tipo"].map(
                lambda tipo: nomes_tipos.get(tipo, tipo)
            )

            df_tipos = df_tipos.rename(columns={
                "tipo": "Tipo",
                "total_titulos": "Total de títulos",
                "titulos_avaliados": "Títulos avaliados",
                "nota_media": "Nota média",
                "total_votos": "Total de votos"
            })

            st.dataframe(
                df_tipos,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total de títulos": st.column_config.NumberColumn(
                        format="%d"
                    ),
                    "Títulos avaliados": st.column_config.NumberColumn(
                        format="%d"
                    ),
                    "Nota média": st.column_config.NumberColumn(
                        format="%.2f"
                    ),
                    "Total de votos": st.column_config.NumberColumn(
                        format="%d"
                    )
                }
            )

        st.divider()

        # 
        # 3. DISTRIBUIÇÃO DAS NOTAS
        # 

        st.subheader("Distribuição das avaliações")

        st.markdown(
            "Visualize como as notas estão distribuídas entre "
            "os títulos avaliados pelo IMDb."
        )

        col1, col2 = st.columns(2)

        with col1:
            tipo_nota = st.selectbox(
                "Tipo de produção",
                options=["movie", "tvSeries"],
                format_func=lambda x: {
                    "movie": "Filmes",
                    "tvSeries": "Séries"
                }[x]
            )

        with col2:
            votos_minimos = st.selectbox(
                "Quantidade mínima de votos",
                options=[100, 1000, 5000, 10000, 50000],
                index=1,
                format_func=lambda x: formatar_numero(x)
            )

        dados_notas = carregar_distribuicao_notas(
            tipo_nota,
            votos_minimos
        )

        if dados_notas:

            df_notas = pd.DataFrame(dados_notas)

            grafico_notas = (
                alt.Chart(df_notas)
                .mark_bar(
                    color=COR_PRIMARIA,
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4
                )
                .encode(
                    x=alt.X(
                        "nota:O",
                        title="Nota IMDb",
                        axis=alt.Axis(
                            labelColor="#9AA3B5",
                            titleColor="#9AA3B5"
                        )
                    ),
                    y=alt.Y(
                        "quantidade:Q",
                        title="Quantidade de títulos",
                        axis=alt.Axis(
                            labelColor="#9AA3B5",
                            titleColor="#9AA3B5",
                            gridColor="#2A3042"
                        )
                    ),
                    tooltip=[
                        alt.Tooltip("nota:O", title="Nota"),
                        alt.Tooltip(
                            "quantidade:Q",
                            title="Quantidade",
                            format=","
                        )
                    ]
                )
                .properties(height=320)
                .configure(
                    background="transparent",
                    view={"stroke": None},
                    axis={"domain": False}
                )
            )

            st.altair_chart(
                grafico_notas,
                use_container_width=True
            )

        else:
            st.info(
                "Não foram encontradas avaliações com esses critérios."
            )

        st.caption(
            "As notas são agrupadas em valores inteiros para facilitar "
            "a visualização da distribuição."
        )

        st.divider()


        # 
        # 2. PRODUÇÃO POR ANO
        # 

        st.subheader("Produção audiovisual por ano")

        st.markdown(
            "Quantidade de filmes e séries lançados entre 1970 e 2025."
        )

        dados_producao = obter_producao_por_ano()

        if dados_producao:

            df_producao = pd.DataFrame(dados_producao)

            df_producao["ano"] = df_producao["ano"].astype(int)

            df_producao = df_producao.melt(
                id_vars=["ano"],
                value_vars=["filmes", "series"],
                var_name="tipo",
                value_name="quantidade"
            )

            df_producao["tipo"] = df_producao["tipo"].map({
                "filmes": "Filmes",
                "series": "Séries"
            })

            grafico_producao = (
                alt.Chart(df_producao)
                .mark_line(
                    point=True,
                    strokeWidth=2.5
                )
                .encode(
                    x=alt.X(
                        "ano:O",
                        title="Ano",
                        axis=alt.Axis(
                            labelAngle=-45,
                            labelColor="#9AA3B5",
                            titleColor="#9AA3B5",
                            grid=False
                        )
                    ),
                    y=alt.Y(
                        "quantidade:Q",
                        title="Quantidade de produções",
                        axis=alt.Axis(
                            labelColor="#9AA3B5",
                            titleColor="#9AA3B5",
                            gridColor="#2A3042"
                        )
                    ),
                    color=alt.Color(
                        "tipo:N",
                        title="Tipo",
                        scale=alt.Scale(
                            domain=["Filmes", "Séries"],
                            range=[COR_PRIMARIA, COR_SECUNDARIA]
                        )
                    ),
                    tooltip=[
                        alt.Tooltip("ano:O", title="Ano"),
                        alt.Tooltip("tipo:N", title="Tipo"),
                        alt.Tooltip(
                            "quantidade:Q",
                            title="Quantidade",
                            format=","
                        )
                    ]
                )
                .properties(height=350)
                .configure(
                    background="transparent",
                    view={"stroke": None},
                    axis={"domain": False}
                )
            )

            st.altair_chart(
                grafico_producao,
                use_container_width=True
            )

        else:
            st.info("Não há dados de produção disponíveis.")

        st.divider()

        # 
        # 3. DURAÇÃO MÉDIA DOS FILMES
        # 

        st.subheader("Evolução da duração média dos filmes")

        st.markdown(
            "Duração média dos filmes por ano, considerando produções "
            "entre 1950 e 2025 com duração entre 30 e 300 minutos."
        )

        dados_duracao = obter_duracao_media_por_ano()

        if dados_duracao:

            df_duracao = pd.DataFrame(dados_duracao)

            grafico_duracao = (
                alt.Chart(df_duracao)
                .mark_line(
                    color=COR_PRIMARIA,
                    point=True,
                    strokeWidth=2.5
                )
                .encode(
                    x=alt.X(
                        "ano:O",
                        title="Ano",
                        axis=alt.Axis(
                            labelAngle=-45,
                            labelColor="#9AA3B5",
                            titleColor="#9AA3B5",
                            grid=False
                        )
                    ),
                    y=alt.Y(
                        "duracao_media:Q",
                        title="Duração média (minutos)",
                        axis=alt.Axis(
                            labelColor="#9AA3B5",
                            titleColor="#9AA3B5",
                            gridColor="#2A3042"
                        )
                    ),
                    tooltip=[
                        alt.Tooltip("ano:O", title="Ano"),
                        alt.Tooltip(
                            "duracao_media:Q",
                            title="Duração média",
                            format=".1f"
                        )
                    ]
                )
                .properties(height=350)
                .configure(
                    background="transparent",
                    view={"stroke": None},
                    axis={"domain": False}
                )
            )

            st.altair_chart(
                grafico_duracao,
                use_container_width=True
            )

        else:
            st.info("Não há dados de duração disponíveis.")

        st.divider()

        # 
        # 4. RANKING POR GÊNERO
        # 

        st.subheader("Filmes mais bem avaliados por gênero")

        st.markdown(
            "Consulte os dez filmes mais bem avaliados de cada gênero, "
            "considerando apenas títulos com pelo menos 50 mil votos."
        )

        generos = {
            "Ação": "Action",
            "Comédia": "Comedy",
            "Drama": "Drama",
            "Ficção científica": "Sci-Fi",
            "Terror": "Horror",
            "Romance": "Romance",
            "Animação": "Animation",
            "Documentário": "Documentary"
        }

        genero_selecionado = st.selectbox(
            "Selecione um gênero",
            options=list(generos.keys())
        )

        dados_top = obter_top_filmes_por_genero(
            generos[genero_selecionado]
        )

        if dados_top:

            df_top = pd.DataFrame(dados_top)

            df_top = df_top.rename(columns={
                "titulo": "Filme",
                "ano": "Ano",
                "nota": "Nota IMDb"
            })

            df_top.index = range(1, len(df_top) + 1)
            df_top.index.name = "Posição"

            st.dataframe(
                df_top,
                use_container_width=True
            )

        else:
            st.info(
                "Não foram encontrados filmes para esse gênero "
                "com os critérios selecionados."
            )

        st.caption(
            "Fonte dos dados: IMDb Non-Commercial Datasets. "
            "Dados sujeitos a atualizações periódicas."
        )

    except Exception as e:

        st.error(
            f"Não foi possível carregar as análises: {e}"
        )
