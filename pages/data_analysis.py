import streamlit as st
import mysql.connector
import pandas as pd

st.set_page_config(
    page_title="Análise de Dados - StreamHub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove totalmente o menu lateral (e o botão de abrir/fechar), mesmo se a página
# estiver dentro de uma pasta "pages/" (que faz o Streamlit gerar navegação automática).
st.markdown(
    """
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] { display: none !important; }
    .block-container { padding-top: 2rem; max-width: 1300px; }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "streaming_data",
    "use_pure": True,  # evita a extensão em C, que causa "double free" com threads do Streamlit
}

TIPOS = {
    "movie": "Filmes",
    "tvSeries": "Séries",
    "tvEpisode": "Episódios",
    "short": "Curtas-metragens",
    "tvMovie": "Filmes para TV",
    "tvMiniSeries": "Minisséries",
    "tvSpecial": "Especiais de TV",
    "video": "Vídeos",
    "videoGame": "Games",
    "tvShort": "Curtas de TV",
}

GENEROS = {
    "Action": "Ação", "Adventure": "Aventura", "Animation": "Animação",
    "Biography": "Biografia", "Comedy": "Comédia", "Crime": "Crime",
    "Documentary": "Documentário", "Drama": "Drama", "Family": "Família",
    "Fantasy": "Fantasia", "History": "História", "Horror": "Terror",
    "Music": "Música", "Musical": "Musical", "Mystery": "Mistério",
    "Romance": "Romance", "Sci-Fi": "Ficção Científica", "Sport": "Esporte",
    "Thriller": "Suspense", "War": "Guerra", "Western": "Faroeste",
}

OPCOES_TIPO = {"Filmes": "movie", "Séries": "tvSeries"}


# -------------------------------------------------------------
# VERIFICAÇÃO / CARGA INICIAL DO BANCO
# -------------------------------------------------------------
def check_database_ready():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM imdb_basics;")
        count_basics = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM imdb_ratings;")
        count_ratings = cursor.fetchone()[0]
        conn.close()
        return count_basics > 0 and count_ratings > 0
    except Exception:
        return False


if not check_database_ready():
    st.title("📊 Análise de Dados do Catálogo")
    st.warning("⚠️ O banco de dados MySQL local ainda não possui os dados do IMDb carregados.")
    if st.button("🚀 Inicializar e Baixar Dados do IMDb", type="primary"):
        with st.spinner("Carregando base de dados... (pode levar alguns minutos)"):
            try:
                from database import setup_database
                setup_database.setup_database()
                st.success("✅ Carga concluída!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao executar a carga: {e}")
    st.stop()


# -------------------------------------------------------------
# CONEXÃO E CACHE DE CONSULTAS
# -------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def run_query(query, params=None):
    # Uma conexão por consulta: nunca é compartilhada entre threads do Streamlit.
    # Como o resultado fica em cache, o custo de abrir a conexão é irrelevante.
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or None)
        rows = cursor.fetchall()
        cursor.close()
    finally:
        conn.close()
    df = pd.DataFrame(rows)
    # Converte decimal.Decimal em números reconhecidos pelos gráficos
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass
    return df


def fmt(n):
    """Formata inteiros no padrão brasileiro: 1.234.567"""
    if pd.isna(n):
        return "—"
    return f"{int(n):,}".replace(",", ".")


# -------------------------------------------------------------
# CABEÇALHO
# -------------------------------------------------------------
st.title("📊 Dashboard Analítico de Conteúdo")
st.write(
    "Métricas de produção, avaliação e comportamento do catálogo de filmes e séries, "
    "calculadas a partir dos datasets públicos do IMDb."
)

with st.expander("ℹ️ Sobre os dados e como interpretar as métricas"):
    st.markdown(
        """
- **Fonte:** datasets públicos do IMDb (`title.basics` e `title.ratings`), carregados no MySQL local.
- **Nota (0 a 10):** média das notas dadas pelos usuários do IMDb. Não é nota de crítica especializada.
- **Votos:** quantidade de usuários que avaliaram o título. Funciona como termômetro de **popularidade**
  e de **confiabilidade da nota**: uma nota 9,5 com 12 votos diz muito menos que uma nota 8,5 com 500 mil votos.
  Por isso os rankings têm um filtro de votos mínimos.
- **Tipo de título:** o IMDb separa filmes, séries, episódios, curtas, etc. Os episódios, sozinhos,
  são a maior parte da base, então aqui o foco são **filmes** e **séries**.
- **Ano:** é o ano de lançamento (para séries, o ano de estreia). Anos muito recentes podem estar incompletos,
  pois o IMDb continua cadastrando títulos novos.
- **Conteúdo adulto** é excluído dos rankings e da análise de gêneros.
        """
    )

aba_geral, aba_producao, aba_generos, aba_rankings = st.tabs(
    ["📌 Visão Geral", "📈 Produção ao Longo do Tempo", "🎭 Gêneros", "🏆 Rankings"]
)

# =============================================================
# ABA 1: VISÃO GERAL
# =============================================================
with aba_geral:
    st.subheader("📌 Visão Geral do Catálogo")
    st.caption(
        "Resumo do tamanho da base e da qualidade média percebida pelo público. "
        "Serve como ponto de partida para entender o que existe no catálogo antes de analisar os detalhes."
    )

    df_tipos = run_query("""
        SELECT b.titleType AS tipo,
               COUNT(*) AS titulos,
               COUNT(r.tconst) AS avaliados,
               ROUND(AVG(r.averageRating), 2) AS nota_media,
               SUM(r.numVotes) AS votos
        FROM imdb_basics b
        LEFT JOIN imdb_ratings r ON b.tconst = r.tconst
        GROUP BY b.titleType
        ORDER BY titulos DESC;
    """)
    df_tipos["Tipo"] = df_tipos["tipo"].map(TIPOS).fillna(df_tipos["tipo"])
    por_tipo = df_tipos.set_index("tipo")

    def kpi(tipo, col):
        return por_tipo[col].get(tipo, float("nan"))

    series_andamento = run_query(
        "SELECT COUNT(*) AS n FROM imdb_basics WHERE titleType = 'tvSeries' AND endYear IS NULL;"
    )["n"][0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🗂️ Total de Títulos", fmt(df_tipos["titulos"].sum()),
              help="Todos os registros da base, de qualquer tipo (inclui episódios, curtas, games etc.).")
    c2.metric("🎬 Filmes", fmt(kpi("movie", "titulos")),
              help="Longas-metragens cadastrados como 'movie'.")
    c3.metric("📺 Séries", fmt(kpi("tvSeries", "titulos")),
              help="Séries de TV/streaming (a série em si, não os episódios).")
    c4.metric("🔄 Séries em Andamento", fmt(series_andamento),
              help="Séries sem ano de término cadastrado. Algumas séries encerradas podem não ter essa informação no IMDb, então é uma estimativa.")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("⭐ Nota Média: Filmes", f"{kpi('movie', 'nota_media'):.2f} / 10",
              help="Média simples das notas de todos os filmes avaliados.")
    c6.metric("⭐ Nota Média: Séries", f"{kpi('tvSeries', 'nota_media'):.2f} / 10",
              help="Média simples das notas de todas as séries avaliadas.")
    c7.metric("🗳️ Votos em Filmes", fmt(kpi("movie", "votos")),
              help="Soma de todas as avaliações de usuários em filmes: indica o engajamento do público.")
    c8.metric("🗳️ Votos em Séries", fmt(kpi("tvSeries", "votos")),
              help="Soma de todas as avaliações de usuários em séries.")

    st.divider()

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("🧩 Composição da Base por Tipo")
        st.caption("Quantos títulos existem de cada formato. Mostra onde está o volume do catálogo.")
        st.bar_chart(df_tipos.set_index("Tipo")["titulos"])
    with col_b:
        st.subheader("📋 Detalhamento por Tipo")
        st.caption("Percentual de títulos com ao menos uma avaliação e a nota média de cada formato.")
        tabela = df_tipos[["Tipo", "titulos", "avaliados", "nota_media"]].copy()
        tabela["% Avaliados"] = (tabela["avaliados"] / tabela["titulos"] * 100).round(1)
        tabela = tabela.rename(columns={"titulos": "Títulos", "avaliados": "Avaliados", "nota_media": "Nota Média"})
        st.dataframe(
            tabela,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Títulos": st.column_config.NumberColumn(format="%d"),
                "Avaliados": st.column_config.NumberColumn(format="%d"),
                "% Avaliados": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "Nota Média": st.column_config.NumberColumn(format="%.2f"),
            },
        )

    st.divider()
    st.subheader("📊 Distribuição das Notas")
    st.caption(
        "Quantos títulos receberam cada nota (arredondada para o inteiro mais próximo). "
        "Ajuda a responder: o público costuma ser generoso ou rigoroso? Quanto mais à direita, melhor avaliado."
    )
    f1, f2 = st.columns(2)
    tipo_dist = f1.radio("Tipo de título", list(OPCOES_TIPO), horizontal=True, key="dist_tipo")
    votos_dist = f2.select_slider(
        "Votos mínimos por título", options=[1, 10, 100, 1000, 10000], value=100, key="dist_votos",
        help="Filtra títulos com poucos votos, cujas notas são menos confiáveis.",
    )
    df_dist = run_query("""
        SELECT ROUND(r.averageRating) AS nota, COUNT(*) AS titulos
        FROM imdb_basics b
        JOIN imdb_ratings r ON b.tconst = r.tconst
        WHERE b.titleType = %s AND r.numVotes >= %s
        GROUP BY nota
        ORDER BY nota;
    """, (OPCOES_TIPO[tipo_dist], votos_dist))
    if df_dist.empty:
        st.info("Nenhum título encontrado com esses filtros.")
    else:
        moda = int(df_dist.loc[df_dist["titulos"].idxmax(), "nota"])
        df_dist["nota"] = df_dist["nota"].astype(int).astype(str)
        st.bar_chart(df_dist.set_index("nota")["titulos"])
        st.caption(f"💡 A maior concentração de {tipo_dist.lower()} está na nota **{moda}**.")

# =============================================================
# ABA 2: PRODUÇÃO AO LONGO DO TEMPO
# =============================================================
with aba_producao:
    st.subheader("📈 Crescimento da Produção: Filmes vs. Séries")
    st.caption(
        "Quantidade de títulos lançados por ano. Mostra como a produção cresceu e "
        "quando as séries ganharam força frente aos filmes (o chamado boom do streaming)."
    )
    anos = st.slider("Período analisado", 1920, 2025, (1970, 2025), key="anos_prod")

    df_prod = run_query("""
        SELECT startYear AS Ano,
               COUNT(CASE WHEN titleType = 'movie' THEN 1 END) AS Filmes,
               COUNT(CASE WHEN titleType = 'tvSeries' THEN 1 END) AS Séries
        FROM imdb_basics
        WHERE titleType IN ('movie', 'tvSeries') AND startYear BETWEEN %s AND %s
        GROUP BY startYear
        ORDER BY startYear;
    """, anos)
    if not df_prod.empty:
        st.area_chart(df_prod.set_index("Ano"))
        pico_f = df_prod.loc[df_prod["Filmes"].idxmax()]
        pico_s = df_prod.loc[df_prod["Séries"].idxmax()]
        m1, m2 = st.columns(2)
        m1.metric("🎬 Ano de pico de filmes", int(pico_f["Ano"]), f"{fmt(pico_f['Filmes'])} títulos", delta_color="off")
        m2.metric("📺 Ano de pico de séries", int(pico_s["Ano"]), f"{fmt(pico_s['Séries'])} títulos", delta_color="off")

    st.divider()
    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.subheader("⏱️ Duração Média dos Filmes")
        st.caption(
            "Duração média (em minutos) dos filmes lançados em cada ano. "
            "Útil para ver se o mercado está produzindo filmes mais longos ou mais curtos. "
            "Considera apenas filmes entre 30 e 300 minutos."
        )
        df_dur = run_query("""
            SELECT startYear AS Ano, ROUND(AVG(runtimeMinutes), 1) AS `Duração Média (min)`
            FROM imdb_basics
            WHERE titleType = 'movie' AND startYear BETWEEN %s AND %s
              AND runtimeMinutes BETWEEN 30 AND 300
            GROUP BY startYear
            ORDER BY startYear;
        """, anos)
        if not df_dur.empty:
            st.line_chart(df_dur.set_index("Ano"))

    with col_dir:
        st.subheader("⭐ Nota Média por Década")
        st.caption(
            "Os títulos de hoje são melhores ou piores que os antigos? Considera só títulos com "
            "ao menos 1.000 votos, para evitar distorções de obras pouco conhecidas."
        )
        df_dec = run_query("""
            SELECT FLOOR(b.startYear / 10) * 10 AS Década,
                   ROUND(AVG(CASE WHEN b.titleType = 'movie' THEN r.averageRating END), 2) AS Filmes,
                   ROUND(AVG(CASE WHEN b.titleType = 'tvSeries' THEN r.averageRating END), 2) AS Séries
            FROM imdb_basics b
            JOIN imdb_ratings r ON b.tconst = r.tconst
            WHERE b.titleType IN ('movie', 'tvSeries')
              AND r.numVotes >= 1000
              AND b.startYear BETWEEN 1920 AND 2029
            GROUP BY Década
            ORDER BY Década;
        """)
        if not df_dec.empty:
            df_dec["Década"] = df_dec["Década"].astype(int).astype(str) + "s"
            st.line_chart(df_dec.set_index("Década"))

# =============================================================
# ABA 3: GÊNEROS
# =============================================================
with aba_generos:
    st.subheader("🎭 Panorama por Gênero")
    st.caption(
        "Compara os gêneros em duas dimensões: **volume** (quantos títulos existem) e **qualidade percebida** "
        "(nota média). Um título pode ter vários gêneros e, nesse caso, entra na contagem de cada um deles."
    )
    g1, g2 = st.columns(2)
    tipo_gen = g1.radio("Tipo de título", list(OPCOES_TIPO), horizontal=True, key="gen_tipo")
    votos_gen = g2.select_slider(
        "Votos mínimos para entrar no cálculo da nota média",
        options=[100, 500, 1000, 5000, 10000], value=1000, key="gen_votos",
    )

    @st.cache_data(ttl=3600, show_spinner="Calculando gêneros...")
    def analise_generos(tipo, min_votos):
        partes = []
        for i, g in enumerate(GENEROS):
            cond = f"FIND_IN_SET('{g}', b.genres) > 0"
            partes.append(f"SUM({cond}) AS n{i}")
            partes.append(f"AVG(CASE WHEN {cond} AND r.numVotes >= {int(min_votos)} THEN r.averageRating END) AS a{i}")
        query = f"""
            SELECT {', '.join(partes)}
            FROM imdb_basics b
            LEFT JOIN imdb_ratings r ON b.tconst = r.tconst
            WHERE b.titleType = %s AND b.isAdult = 0;
        """
        row = run_query(query, (tipo,)).iloc[0]
        return pd.DataFrame([
            {"Gênero": pt, "Títulos": row[f"n{i}"], "Nota Média": row[f"a{i}"]}
            for i, pt in enumerate(GENEROS.values())
        ])

    df_gen = analise_generos(OPCOES_TIPO[tipo_gen], votos_gen)
    cfg = {
        "Títulos": st.column_config.ProgressColumn(
            format="%d", min_value=0, max_value=float(df_gen["Títulos"].max())),
        "Nota Média": st.column_config.ProgressColumn(
            format="%.2f", min_value=0, max_value=10),
    }

    cg1, cg2 = st.columns(2)
    with cg1:
        st.markdown("**📚 Gêneros com mais títulos**")
        st.caption("Onde está o maior volume de produção.")
        st.dataframe(df_gen.sort_values("Títulos", ascending=False), hide_index=True,
                     use_container_width=True, column_config=cfg, height=500)
    with cg2:
        st.markdown("**🌟 Gêneros mais bem avaliados**")
        st.caption("Gêneros cujo público tende a dar notas mais altas.")
        st.dataframe(df_gen.dropna(subset=["Nota Média"]).sort_values("Nota Média", ascending=False),
                     hide_index=True, use_container_width=True, column_config=cfg, height=500)

    melhor = df_gen.dropna(subset=["Nota Média"]).sort_values("Nota Média", ascending=False).iloc[0]
    maior = df_gen.sort_values("Títulos", ascending=False).iloc[0]
    st.info(
        f"💡 Entre {tipo_gen.lower()}, **{maior['Gênero']}** é o gênero mais produzido "
        f"({fmt(maior['Títulos'])} títulos) e **{melhor['Gênero']}** tem a maior nota média "
        f"({melhor['Nota Média']:.2f})."
    )

# =============================================================
# ABA 4: RANKINGS
# =============================================================
with aba_rankings:
    st.subheader("🏆 Rankings de Títulos")
    st.caption(
        "Listas dos títulos que mais se destacam. Use os filtros para refinar por tipo, gênero e período. "
        "Clique em “Abrir” para ver a página do título no IMDb."
    )

    r1, r2, r3 = st.columns(3)
    tipo_rk = r1.radio("Tipo de título", list(OPCOES_TIPO), horizontal=True, key="rk_tipo")
    genero_rk = r2.selectbox("Gênero", ["Todos"] + list(GENEROS.values()), key="rk_genero")
    anos_rk = r3.slider("Ano de lançamento", 1920, 2025, (1990, 2025), key="rk_anos")

    min_votos_rk = st.select_slider(
        "Votos mínimos (rankings de nota e de popularidade)",
        options=[1000, 5000, 10000, 25000, 50000, 100000, 250000], value=50000, key="rk_votos",
        help="Quanto maior, mais consolidado e conhecido é o título. Quanto menor, mais títulos de nicho aparecem.",
    )

    GEN_EN = {pt: en for en, pt in GENEROS.items()}

    def ranking(ordem, min_votos, max_votos=None, limite=15):
        where = ["b.titleType = %s", "r.numVotes >= %s", "b.startYear BETWEEN %s AND %s", "b.isAdult = 0"]
        params = [OPCOES_TIPO[tipo_rk], min_votos, anos_rk[0], anos_rk[1]]
        if max_votos:
            where.append("r.numVotes <= %s")
            params.append(max_votos)
        if genero_rk != "Todos":
            where.append("FIND_IN_SET(%s, b.genres) > 0")
            params.append(GEN_EN[genero_rk])
        order_sql = "r.averageRating DESC, r.numVotes DESC" if ordem == "nota" else "r.numVotes DESC"
        df = run_query(f"""
            SELECT b.tconst, b.primaryTitle AS `Título`, b.startYear AS `Ano`,
                   b.genres AS `Gêneros`, b.runtimeMinutes AS `Duração (min)`,
                   r.averageRating AS `Nota`, r.numVotes AS `Votos`
            FROM imdb_basics b
            JOIN imdb_ratings r ON b.tconst = r.tconst
            WHERE {' AND '.join(where)}
            ORDER BY {order_sql}
            LIMIT {int(limite)};
        """, tuple(params))
        if not df.empty:
            df["IMDb"] = "https://www.imdb.com/title/" + df["tconst"] + "/"
            df = df.drop(columns="tconst")
        return df

    rk_cfg = {
        "Nota": st.column_config.NumberColumn(format="%.1f ⭐"),
        "Votos": st.column_config.NumberColumn(format="%d"),
        "Ano": st.column_config.NumberColumn(format="%d"),
        "Duração (min)": st.column_config.NumberColumn(format="%d"),
        "IMDb": st.column_config.LinkColumn(display_text="Abrir"),
    }

    def mostrar(df):
        if df.empty:
            st.info("Nenhum título encontrado com esses filtros. Tente reduzir os votos mínimos ou ampliar o período.")
        else:
            st.dataframe(df, hide_index=True, use_container_width=True, column_config=rk_cfg)

    st.markdown("### ⭐ Mais bem avaliados")
    st.caption("Os títulos com as maiores notas entre os que atingiram o mínimo de votos. É a lista dos “consenso de qualidade”.")
    mostrar(ranking("nota", min_votos_rk))

    st.markdown("### 🔥 Mais populares")
    st.caption("Os títulos com mais avaliações, ou seja, os que mais mobilizaram o público, independentemente de serem os melhores.")
    mostrar(ranking("votos", min_votos_rk))

    st.markdown("### 💎 Joias escondidas")
    st.caption(
        "Títulos muito bem avaliados, mas ainda pouco conhecidos (entre 2.000 e 30.000 votos). "
        "Boa fonte de recomendações fora do óbvio e de oportunidades de catálogo."
    )
    mostrar(ranking("nota", 2000, max_votos=30000))

st.divider()
st.caption("Fonte: IMDb Non-Commercial Datasets · Dados armazenados em MySQL local · Consultas em cache por 1 hora.")