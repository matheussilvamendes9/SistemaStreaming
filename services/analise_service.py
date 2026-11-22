from database.connection import consultar



# 1. INDICADORES GERAIS DO IMDB


def obter_indicadores_imdb():
    sql = """
        SELECT
            COUNT(CASE WHEN b.titleType = 'movie' THEN 1 END)
                AS total_filmes,

            COUNT(CASE WHEN b.titleType = 'tvSeries' THEN 1 END)
                AS total_series,

            ROUND(AVG(r.averageRating), 2)
                AS nota_media

        FROM imdb_basics b
        LEFT JOIN imdb_ratings r
            ON b.tconst = r.tconst;
    """

    resultado = consultar(sql, banco="analise")

    return resultado[0]



# 2. PRODUÇÃO DE FILMES E SÉRIES POR ANO


def obter_producao_por_ano():
    sql = """
        SELECT
            startYear AS ano,

            COUNT(
                CASE WHEN titleType = 'movie' THEN 1 END
            ) AS filmes,

            COUNT(
                CASE WHEN titleType = 'tvSeries' THEN 1 END
            ) AS series

        FROM imdb_basics

        WHERE titleType IN ('movie', 'tvSeries')
          AND startYear BETWEEN 1970 AND 2025

        GROUP BY startYear
        ORDER BY startYear;
    """

    return consultar(sql, banco="analise")



# 3. MÉDIA DE DURAÇÃO DOS FILMES POR ANO


def obter_duracao_media_por_ano():
    sql = """
        SELECT
            startYear AS ano,
            ROUND(AVG(runtimeMinutes), 1) AS duracao_media

        FROM imdb_basics

        WHERE titleType = 'movie'
          AND startYear BETWEEN 1950 AND 2025
          AND runtimeMinutes BETWEEN 30 AND 300

        GROUP BY startYear
        ORDER BY startYear;
    """

    return consultar(sql, banco="analise")



# 4. TOP 10 FILMES POR GÊNERO


def obter_top_filmes_por_genero(genero):
    sql = """
        SELECT
            b.primaryTitle AS titulo,
            b.startYear AS ano,
            r.averageRating AS nota

        FROM imdb_basics b

        INNER JOIN imdb_ratings r
            ON b.tconst = r.tconst

        WHERE b.titleType = 'movie'
          AND b.genres LIKE %s
          AND r.numVotes >= 50000

        ORDER BY r.averageRating DESC

        LIMIT 10;
    """

    return consultar(
        sql,
        (f"%{genero}%",),
        banco="analise"
    )



# 5. INDICADORES AGRUPADOS POR TIPO DE PRODUÇÃO


def obter_resumo_por_tipo():
    sql = """
        SELECT
            b.titleType AS tipo,
            COUNT(*) AS total_titulos,
            COUNT(r.tconst) AS titulos_avaliados,
            ROUND(AVG(r.averageRating), 2) AS nota_media,
            COALESCE(SUM(r.numVotes), 0) AS total_votos

        FROM imdb_basics b

        LEFT JOIN imdb_ratings r
            ON b.tconst = r.tconst

        GROUP BY b.titleType
        ORDER BY total_titulos DESC;
    """

    return consultar(sql, banco="analise")



# 6. SÉRIES SEM ANO DE TÉRMINO CADASTRADO


def obter_series_sem_ano_termino():
    sql = """
        SELECT COUNT(*) AS total
        FROM imdb_basics
        WHERE titleType = 'tvSeries'
          AND endYear IS NULL;
    """

    resultado = consultar(sql, banco="analise")

    return resultado[0]["total"]



# 7. DISTRIBUIÇÃO DAS NOTAS POR TIPO DE PRODUÇÃO


def obter_distribuicao_notas(tipo, votos_minimos):
    sql = """
        SELECT
            ROUND(r.averageRating) AS nota,
            COUNT(*) AS quantidade

        FROM imdb_basics b

        INNER JOIN imdb_ratings r
            ON b.tconst = r.tconst

        WHERE b.titleType = %s
          AND r.numVotes >= %s

        GROUP BY ROUND(r.averageRating)
        ORDER BY nota;
    """

    return consultar(
        sql,
        (tipo, votos_minimos),
        banco="analise"
    )
