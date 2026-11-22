
import gzip
import os
import shutil
import tempfile
import urllib.request

from database.connection import get_connection


URLS = {
    "basics": "https://datasets.imdbws.com/title.basics.tsv.gz",
    "ratings": "https://datasets.imdbws.com/title.ratings.tsv.gz"
}


def baixar_e_extrair(url, destino):
    """Baixa um arquivo .gz do IMDb e extrai o TSV."""

    arquivo_gz = destino + ".gz"

    print(f"Baixando: {url}")

    urllib.request.urlretrieve(url, arquivo_gz)

    print(f"Extraindo: {destino}")

    with gzip.open(arquivo_gz, "rb") as origem:
        with open(destino, "wb") as saida:
            shutil.copyfileobj(origem, saida)

    os.remove(arquivo_gz)


def criar_tabelas(cursor):
    """Cria as tabelas analíticas caso ainda não existam."""

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
        ) ENGINE=InnoDB;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imdb_ratings (
            tconst VARCHAR(15) PRIMARY KEY,
            averageRating DECIMAL(3,1),
            numVotes INT
        ) ENGINE=InnoDB;
    """)


def importar_basics(cursor, caminho):
    """Importa os dados básicos dos títulos."""

    caminho_sql = caminho.replace("\\", "/")

    sql = f"""
        LOAD DATA LOCAL INFILE '{caminho_sql}'
        INTO TABLE imdb_basics
        CHARACTER SET utf8mb4
        FIELDS TERMINATED BY '\\t'
        LINES TERMINATED BY '\\n'
        IGNORE 1 LINES
        (
            tconst,
            titleType,
            primaryTitle,
            originalTitle,
            isAdult,
            @startYear,
            @endYear,
            @runtimeMinutes,
            genres
        )
        SET
            startYear = NULLIF(@startYear, '\\\\N'),
            endYear = NULLIF(@endYear, '\\\\N'),
            runtimeMinutes = NULLIF(@runtimeMinutes, '\\\\N');
    """

    cursor.execute(sql)


def importar_ratings(cursor, caminho):
    """Importa as notas e quantidade de votos dos títulos."""

    caminho_sql = caminho.replace("\\", "/")

    sql = f"""
        LOAD DATA LOCAL INFILE '{caminho_sql}'
        INTO TABLE imdb_ratings
        CHARACTER SET utf8mb4
        FIELDS TERMINATED BY '\\t'
        LINES TERMINATED BY '\\n'
        IGNORE 1 LINES
        (
            tconst,
            averageRating,
            numVotes
        );
    """

    cursor.execute(sql)


def setup_analise():
    """Prepara e importa os dados do IMDb no banco analise_db."""

    print("Conectando ao banco analise_db...")

    conn = get_connection(
        banco="analise",
        allow_local_infile=True
    )

    cursor = conn.cursor()

    try:
        criar_tabelas(cursor)
        conn.commit()

        # Verifica se as tabelas já possuem dados.
        cursor.execute("SELECT COUNT(*) FROM imdb_basics")
        total_basics = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM imdb_ratings")
        total_ratings = cursor.fetchone()[0]

        if total_basics > 0 or total_ratings > 0:
            print("A importação foi interrompida.")
            print("As tabelas já possuem dados.")
            print("Nenhum registro foi apagado.")
            return

        with tempfile.TemporaryDirectory(
            prefix="streamhub_imdb_"
        ) as pasta_temp:

            basics_path = os.path.join(
                pasta_temp,
                "title.basics.tsv"
            )

            ratings_path = os.path.join(
                pasta_temp,
                "title.ratings.tsv"
            )

            # Download e extração.
            baixar_e_extrair(
                URLS["basics"],
                basics_path
            )

            baixar_e_extrair(
                URLS["ratings"],
                ratings_path
            )

            # Importação.
            print("Importando títulos...")

            importar_basics(cursor, basics_path)
            conn.commit()

            print("Importando avaliações...")

            importar_ratings(cursor, ratings_path)
            conn.commit()

        print("Importação concluída!")

        cursor.execute("SELECT COUNT(*) FROM imdb_basics")
        total_basics = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM imdb_ratings")
        total_ratings = cursor.fetchone()[0]

        print(f"Títulos importados: {total_basics:,}")
        print(f"Avaliações importadas: {total_ratings:,}")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    setup_analise()
