"""RF04 - CRUD de assinaturas (sem cobranca real)."""
from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import (validar_data, validar_inteiro, validar_opcao,
                                 validar_valor_monetario)

PLANOS = ("basico", "padrao", "premium")
STATUS = ("ativa", "cancelada", "expirada")


def _validar(id_usuario, plano, valor, data_inicio, data_termino, status):
    id_usuario = validar_inteiro(id_usuario, "usuario", 1)
    plano = validar_opcao(plano, PLANOS, "plano")
    valor = validar_valor_monetario(valor)
    inicio = validar_data(data_inicio, "data de inicio")
    termino = validar_data(data_termino, "data de termino", obrigatoria=False)
    status = validar_opcao(status, STATUS, "status")
    if termino and termino < inicio:
        raise ErroAplicacao("A data de termino nao pode ser anterior a data de inicio.")
    return id_usuario, plano, valor, inicio, termino, status


def listar_assinaturas(id_usuario=None, status=None):
    sql = """
        SELECT a.id_assinatura, a.id_usuario, u.nome AS usuario, a.plano, a.valor,
               a.data_inicio, a.data_termino, a.status
        FROM assinatura a JOIN usuario u ON u.id_usuario = a.id_usuario
        WHERE 1 = 1
    """
    params = []
    if id_usuario:
        sql += " AND a.id_usuario = %s"
        params.append(id_usuario)
    if status in STATUS:
        sql += " AND a.status = %s"
        params.append(status)
    sql += " ORDER BY a.data_inicio DESC"
    return consultar(sql, tuple(params))


def criar_assinatura(id_usuario, plano, valor, data_inicio, data_termino=None, status="ativa"):
    dados = _validar(id_usuario, plano, valor, data_inicio, data_termino, status)
    return executar(
        "INSERT INTO assinatura (id_usuario, plano, valor, data_inicio, data_termino, status) "
        "VALUES (%s, %s, %s, %s, %s, %s)", dados)


def atualizar_assinatura(id_assinatura, id_usuario, plano, valor, data_inicio,
                         data_termino=None, status="ativa"):
    dados = _validar(id_usuario, plano, valor, data_inicio, data_termino, status)
    executar(
        "UPDATE assinatura SET id_usuario=%s, plano=%s, valor=%s, data_inicio=%s, "
        "data_termino=%s, status=%s WHERE id_assinatura=%s", (*dados, id_assinatura))


def excluir_assinatura(id_assinatura):
    r = consultar("SELECT 1 FROM assinatura WHERE id_assinatura = %s", (id_assinatura,))
    if not r:
        raise ErroAplicacao("Assinatura nao encontrada.")
    executar("DELETE FROM assinatura WHERE id_assinatura = %s", (id_assinatura,))