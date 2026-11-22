"""RF05 - Historico de reproducao (simulado).

Regras do banco: filme NAO tem episodio; serie EXIGE o episodio assistido.
"""
from datetime import datetime

from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import validar_decimal, validar_inteiro


def registrar_reproducao(id_usuario, id_conteudo, progresso_minutos,
                         id_episodio=None, data_hora=None):
    id_usuario = validar_inteiro(id_usuario, "usuario", 1)
    id_conteudo = validar_inteiro(id_conteudo, "conteudo", 1)
    progresso = validar_decimal(progresso_minutos, "progresso (minutos)", minimo=0)
    data_hora = data_hora or datetime.now()

    if not consultar("SELECT 1 FROM usuario WHERE id_usuario = %s", (id_usuario,)):
        raise ErroAplicacao("Usuario nao encontrado.")

    conteudo = consultar(
        "SELECT tipo, duracao_minutos FROM conteudo WHERE id_conteudo = %s", (id_conteudo,))
    if not conteudo:
        raise ErroAplicacao("Conteudo nao encontrado.")

    if conteudo[0]["tipo"] == "filme":
        if id_episodio not in (None, ""):
            raise ErroAplicacao("Filmes nao possuem episodios.")
        id_episodio = None
        duracao = conteudo[0]["duracao_minutos"]
    else:  # serie
        if id_episodio in (None, ""):
            raise ErroAplicacao("Para series, informe o episodio assistido.")
        id_episodio = validar_inteiro(id_episodio, "episodio", 1)
        ep = consultar(
            "SELECT duracao_minutos FROM episodio WHERE id_episodio = %s AND id_serie = %s",
            (id_episodio, id_conteudo))
        if not ep:
            raise ErroAplicacao("Episodio nao encontrado nesta serie.")
        duracao = ep[0]["duracao_minutos"]

    if duracao and progresso > duracao:
        raise ErroAplicacao(f"O progresso nao pode ultrapassar a duracao ({duracao} min).")

    return executar(
        "INSERT INTO historico_reproducao "
        "(id_usuario, id_conteudo, id_episodio, data_hora, progresso_minutos) "
        "VALUES (%s, %s, %s, %s, %s)",
        (id_usuario, id_conteudo, id_episodio, data_hora, progresso))


def listar_historico(id_usuario=None, limite=200):
    sql = """
        SELECT h.id_reproducao, u.nome AS usuario, c.titulo AS conteudo, c.tipo,
               e.temporada, e.episodio, e.titulo AS titulo_episodio,
               h.data_hora, h.progresso_minutos
        FROM historico_reproducao h
        JOIN usuario  u ON u.id_usuario  = h.id_usuario
        JOIN conteudo c ON c.id_conteudo = h.id_conteudo
        LEFT JOIN episodio e ON e.id_episodio = h.id_episodio
    """
    params = []
    if id_usuario:
        sql += " WHERE h.id_usuario = %s"
        params.append(id_usuario)
    sql += " ORDER BY h.data_hora DESC, h.id_reproducao DESC LIMIT %s"
    params.append(int(limite))
    return consultar(sql, tuple(params))


def excluir_reproducao(id_reproducao):
    executar("DELETE FROM historico_reproducao WHERE id_reproducao = %s", (id_reproducao,))