"""RF05 - Historico de reproducao (simulado)."""
from datetime import datetime

from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import validar_inteiro


def registrar_reproducao(id_usuario, id_conteudo, progresso_minutos, data_hora=None):
    id_usuario = validar_inteiro(id_usuario, "usuario", 1)
    id_conteudo = validar_inteiro(id_conteudo, "conteudo", 1)
    progresso = validar_inteiro(progresso_minutos, "progresso (minutos)", 0)
    data_hora = data_hora or datetime.now()

    conteudo = consultar(
        "SELECT tipo, duracao_minutos FROM conteudo WHERE id_conteudo = %s", (id_conteudo,))
    if not conteudo:
        raise ErroAplicacao("Conteudo nao encontrado.")
    duracao = conteudo[0]["duracao_minutos"]
    if duracao and progresso > duracao:
        raise ErroAplicacao(f"O progresso nao pode ultrapassar a duracao ({duracao} min).")

    return executar(
        "INSERT INTO historico_reproducao (id_usuario, id_conteudo, data_hora, progresso_minutos) "
        "VALUES (%s, %s, %s, %s)", (id_usuario, id_conteudo, data_hora, progresso))


def listar_historico(id_usuario=None, limite=200):
    sql = """
        SELECT h.id_reproducao, u.nome AS usuario, c.titulo AS conteudo, c.tipo,
               h.data_hora, h.progresso_minutos
        FROM historico_reproducao h
        JOIN usuario u  ON u.id_usuario  = h.id_usuario
        JOIN conteudo c ON c.id_conteudo = h.id_conteudo
    """
    params = []
    if id_usuario:
        sql += " WHERE h.id_usuario = %s"
        params.append(id_usuario)
    sql += " ORDER BY h.data_hora DESC LIMIT %s"
    params.append(int(limite))
    return consultar(sql, tuple(params))


def excluir_reproducao(id_reproducao):
    executar("DELETE FROM historico_reproducao WHERE id_reproducao = %s", (id_reproducao,))