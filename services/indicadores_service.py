"""RF07 - Indicadores calculados direto do banco operacional."""
from database.connection import consultar


def obter_indicadores(limite_top=5):
    resumo = consultar("""
        SELECT
          (SELECT COUNT(*) FROM usuario)                              AS total_usuarios,
          (SELECT COUNT(*) FROM conteudo WHERE tipo = 'filme')        AS total_filmes,
          (SELECT COUNT(*) FROM conteudo WHERE tipo = 'serie')        AS total_series,
          (SELECT COUNT(*) FROM historico_reproducao)                 AS total_reproducoes,
          (SELECT COUNT(*) FROM assinatura WHERE status = 'ativa')    AS assinaturas_ativas
    """)[0]
    resumo["top_conteudos"] = consultar("""
        SELECT c.id_conteudo, c.titulo, c.tipo, COUNT(h.id_reproducao) AS total_reproducoes
        FROM conteudo c
        LEFT JOIN historico_reproducao h ON h.id_conteudo = c.id_conteudo
        GROUP BY c.id_conteudo, c.titulo, c.tipo
        ORDER BY total_reproducoes DESC, c.titulo
        LIMIT %s
    """, (int(limite_top),))
    return resumo