"""Consultas auxiliares para checagem de permissão na API (arquivo NOVO)."""
from database.connection import consultar


def obter_reproducao(id_reproducao):
    r = consultar(
        "SELECT id_reproducao, id_usuario FROM historico_reproducao WHERE id_reproducao = %s",
        (id_reproducao,))
    return r[0] if r else None
