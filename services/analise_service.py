"""RF08/RF09 - Consultas estatisticas no Banco A (dados publicos).
EXEMPLO: ajustar tabelas/colunas conforme o dataset escolhido."""
from database.connection import consultar

B = "analise"


def resumo_geral():
    return consultar("""
        SELECT COUNT(*) AS total_registros,
               AVG(horas_media_mensal) AS media_horas,
               MAX(horas_media_mensal) AS maior_media_horas,
               MIN(horas_media_mensal) AS menor_media_horas
        FROM consumo_streaming
    """, banco=B)[0]


def media_horas_por_regiao():
    return consultar("""
        SELECT regiao, ROUND(AVG(horas_media_mensal), 2) AS media_horas
        FROM consumo_streaming GROUP BY regiao ORDER BY media_horas DESC
    """, banco=B)


def assinantes_por_plataforma():
    return consultar("""
        SELECT plataforma, SUM(assinantes) AS total_assinantes
        FROM consumo_streaming GROUP BY plataforma ORDER BY total_assinantes DESC
    """, banco=B)


def evolucao_por_ano():
    return consultar("""
        SELECT ano, SUM(assinantes) AS total_assinantes,
               ROUND(AVG(horas_media_mensal), 2) AS media_horas
        FROM consumo_streaming GROUP BY ano ORDER BY ano
    """, banco=B)