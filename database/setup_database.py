import gzip
import os
import shutil
import urllib.request
import mysql.connector

# Configurações do Banco de Dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root"
}

URLS = {
    "basics": "https://datasets.imdbws.com/title.basics.tsv.gz",
    "ratings": "https://datasets.imdbws.com/title.ratings.tsv.gz"
}

TMP_DIR = "/tmp" if os.name != 'nt' else os.environ.get('TEMP', 'C:\\temp')

def download_and_extract(url, target_tsv):
    gz_path = os.path.join(TMP_DIR, "temp_imdb.gz")
    print(f"⬇️ Baixando {url}...")
    urllib.request.urlretrieve(url, gz_path)
    
    print(f"📦 Descompactando em {target_tsv}...")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(target_tsv, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    if os.path.exists(gz_path):
        os.remove(gz_path)

def setup_database():
    # 1. Conecta ao MySQL e garante a existência da Database
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS streaming_data;")
    conn.close()

    # 2. Conecta à database criada
    DB_CONFIG["database"] = "streaming_data"
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 3. Criação das Tabelas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imdb_basics (
        tconst VARCHAR(15) PRIMARY KEY,
        titleType VARCHAR(50),
        primaryTitle VARCHAR(500),
        originalTitle VARCHAR(500),
        isAdult TINYINT,
        startYear INT,
        endYear INT,
        runtimeMinutes INT,
        genres VARCHAR(255)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imdb_ratings (
        tconst VARCHAR(15) PRIMARY KEY,
        averageRating DECIMAL(3,1),
        numVotes INT
    );
    """)

    # --- NOVO: Limpa as tabelas para evitar o erro Duplicate entry 1062 ---
    cursor.execute("TRUNCATE TABLE imdb_basics;")
    cursor.execute("TRUNCATE TABLE imdb_ratings;")

    # 4. Processamento dos Arquivos
    basics_tsv = os.path.join(TMP_DIR, "title.basics.tsv")
    ratings_tsv = os.path.join(TMP_DIR, "title.ratings.tsv")

    if not os.path.exists(basics_tsv):
        download_and_extract(URLS["basics"], basics_tsv)
    
    if not os.path.exists(ratings_tsv):
        download_and_extract(URLS["ratings"], ratings_tsv)

    # 5. Carga dos Dados (LOAD DATA INFILE)
    load_basics_sql = f"""
    LOAD DATA INFILE '{basics_tsv.replace('\\', '/')}'
    INTO TABLE imdb_basics
    CHARACTER SET utf8mb4
    FIELDS TERMINATED BY '\\t'
    ENCLOSED BY ''
    LINES TERMINATED BY '\\n'
    IGNORE 1 LINES
    (tconst, titleType, primaryTitle, originalTitle, isAdult, @startYear, @endYear, @runtimeMinutes, genres)
    SET 
        startYear = NULLIF(@startYear, '\\\\N'),
        endYear = NULLIF(@endYear, '\\\\N'),
        runtimeMinutes = NULLIF(@runtimeMinutes, '\\\\N');
    """
    cursor.execute(load_basics_sql)
    conn.commit()

    load_ratings_sql = f"""
    LOAD DATA INFILE '{ratings_tsv.replace('\\', '/')}'
    INTO TABLE imdb_ratings
    CHARACTER SET utf8mb4
    FIELDS TERMINATED BY '\\t'
    ENCLOSED BY ''
    LINES TERMINATED BY '\\n'
    IGNORE 1 LINES
    (tconst, averageRating, numVotes);
    """
    cursor.execute(load_ratings_sql)
    conn.commit()

    conn.close()

if __name__ == "__main__":
    setup_database()