import streamlit as st
import mysql.connector
import pandas as pd

st.set_page_config(page_title="Análise de Dados - StreamHub", page_icon="📊", layout="wide")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "streaming_data"
}

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
        with st.spinner("Carregando base de dados..."):
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
st.title("📊 Dashboard Analítico de Conteúdo")
st.write("Métricas de produção, avaliação e comportamento do catálogo do IMDb.")

@st.cache_resource
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

@st.cache_data
def run_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    df = pd.DataFrame(cursor.fetchall())
    
    # Converte colunas decimal.Decimal em números (float/int) reconhecidos pelos gráficos
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')
        
    return df

# -------------------------------------------------------------
# 1. CARDS DE MÉTRICAS (KPIs)
# -------------------------------------------------------------
st.subheader("📌 Visão Geral do Catálogo")

query_kpis = """
SELECT 
    COUNT(CASE WHEN titleType = 'movie' THEN 1 END) AS total_filmes,
    COUNT(CASE WHEN titleType = 'tvSeries' THEN 1 END) AS total_series,
    ROUND(AVG(r.averageRating), 2) AS nota_media
FROM imdb_basics b
LEFT JOIN imdb_ratings r ON b.tconst = r.tconst;
"""
df_kpis = run_query(query_kpis)

col1, col2, col3 = st.columns(3)
col1.metric("🎬 Total de Filmes", f"{df_kpis['total_filmes'][0]:,}".replace(",", "."))
col2.metric("📺 Total de Séries", f"{df_kpis['total_series'][0]:,}".replace(",", "."))
col3.metric("⭐ Nota Média Global", f"{df_kpis['nota_media'][0]} / 10")

st.divider()

# -------------------------------------------------------------
# 2. EVOLUÇÃO TEMPORAL: FILMES VS SÉRIES
# -------------------------------------------------------------
st.subheader("📈 Crescimento da Produção: Filmes vs. Séries (1970 - 2025)")

query_tipos = """
SELECT 
    startYear AS 'Ano',
    COUNT(CASE WHEN titleType = 'movie' THEN 1 END) AS 'Filmes',
    COUNT(CASE WHEN titleType = 'tvSeries' THEN 1 END) AS 'Séries'
FROM imdb_basics
WHERE titleType IN ('movie', 'tvSeries') 
  AND startYear BETWEEN 1970 AND 2025
GROUP BY startYear
ORDER BY startYear;
"""
df_tipos = run_query(query_tipos)
df_tipos.set_index('Ano', inplace=True)
st.area_chart(df_tipos)

# -------------------------------------------------------------
# 3. TENDÊNCIA DE DURAÇÃO DOS FILMES
# -------------------------------------------------------------
col_esq, col_dir = st.columns(2)

with col_esq:
    st.subheader("⏱️ Média de Duração dos Filmes (Minutos)")
    st.write("Como a duração média dos filmes oscilou ao longo dos anos.")

    query_duracao = """
    SELECT 
        startYear AS 'Ano',
        ROUND(AVG(runtimeMinutes), 1) AS 'Duração Média (min)'
    FROM imdb_basics
    WHERE titleType = 'movie' 
      AND startYear BETWEEN 1950 AND 2025
      AND runtimeMinutes BETWEEN 30 AND 300
    GROUP BY startYear
    ORDER BY startYear;
    """
    df_duracao = run_query(query_duracao)
    df_duracao.set_index('Ano', inplace=True)
    st.line_chart(df_duracao)

# -------------------------------------------------------------
# 4. RANKING DINÂMICO POR GÊNERO (FILTRO INTERATIVO)
# -------------------------------------------------------------
with col_dir:
    st.subheader("🏆 Top Filmes por Gênero")
    
    generos_populares = ["Action", "Comedy", "Drama", "Sci-Fi", "Horror", "Romance", "Animation", "Documentary"]
    genero_selecionado = st.selectbox("Selecione o Gênero:", generos_populares)

    query_genero = """
    SELECT 
        b.primaryTitle AS 'Título',
        b.startYear AS 'Ano',
        r.averageRating AS 'Nota'
    FROM imdb_basics b
    JOIN imdb_ratings r ON b.tconst = r.tconst
    WHERE b.titleType = 'movie'
      AND b.genres LIKE %s
      AND r.numVotes >= 50000
    ORDER BY r.averageRating DESC
    LIMIT 10;
    """
    
    df_genero = run_query(query_genero, (f"%{genero_selecionado}%",))
    st.dataframe(df_genero, hide_index=True, use_container_width=True)