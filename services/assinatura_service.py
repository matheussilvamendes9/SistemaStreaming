"""RF04 - CRUD de assinaturas (sem cobranca real)."""
from datetime import date

from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.plano_service import obter_plano
from services.validators import (validar_data, validar_inteiro, validar_opcao,
                                 validar_valor_monetario)

STATUS = ("ativa", "cancelada", "expirada")


def _validar(id_usuario, id_plano, data_inicio, data_termino, status, valor):
    id_usuario = validar_inteiro(id_usuario, "usuario", 1)
    id_plano = validar_inteiro(id_plano, "plano", 1)
    inicio = validar_data(data_inicio, "data de inicio")
    termino = validar_data(data_termino, "data de termino", obrigatoria=False)
    status = validar_opcao(status, STATUS, "status")

    # Regras do banco (CHECK): ativa nao tem termino; as demais exigem termino.
    if status == "ativa" and termino:
        raise ErroAplicacao("Assinatura ativa nao pode ter data de termino.")
    if status != "ativa" and not termino:
        raise ErroAplicacao("Assinatura cancelada ou expirada exige data de termino.")
    if termino and termino < inicio:
        raise ErroAplicacao("A data de termino nao pode ser anterior a data de inicio.")

    plano = obter_plano(id_plano)
    if not plano:
        raise ErroAplicacao("Plano nao encontrado.")
    # Sem valor informado, usa o valor atual do plano.
    valor = validar_valor_monetario(plano["valor"] if valor in (None, "") else valor)
    return id_usuario, id_plano, valor, inicio, termino, status


def listar_assinaturas(id_usuario=None, status=None):
    sql = """
        SELECT a.id_assinatura, a.id_usuario, u.nome AS usuario,
               a.id_plano, p.nome AS plano, a.valor,
               a.data_inicio, a.data_termino, a.status
        FROM assinatura a
        JOIN usuario u ON u.id_usuario = a.id_usuario
        JOIN plano p   ON p.id_plano   = a.id_plano
        WHERE 1 = 1
    """
    params = []
    if id_usuario:
        sql += " AND a.id_usuario = %s"
        params.append(id_usuario)
    if status in STATUS:
        sql += " AND a.status = %s"
        params.append(status)
    sql += " ORDER BY a.data_inicio DESC, a.id_assinatura DESC"
    return consultar(sql, tuple(params))


def obter_assinatura(id_assinatura):
    r = consultar("SELECT * FROM assinatura WHERE id_assinatura = %s", (id_assinatura,))
    return r[0] if r else None


def criar_assinatura(id_usuario, id_plano, data_inicio, data_termino=None,
                     status="ativa", valor=None):
    """Um usuario so pode ter UMA assinatura ativa (o banco recusa a segunda)."""
    dados = _validar(id_usuario, id_plano, data_inicio, data_termino, status, valor)
    return executar(
        "INSERT INTO assinatura (id_usuario, id_plano, valor, data_inicio, data_termino, status) "
        "VALUES (%s, %s, %s, %s, %s, %s)", dados)


def atualizar_assinatura(id_assinatura, id_usuario, id_plano, data_inicio,
                         data_termino=None, status="ativa", valor=None):
    dados = _validar(id_usuario, id_plano, data_inicio, data_termino, status, valor)
    executar(
        "UPDATE assinatura SET id_usuario=%s, id_plano=%s, valor=%s, data_inicio=%s, "
        "data_termino=%s, status=%s WHERE id_assinatura=%s", (*dados, id_assinatura))


def encerrar_assinatura(id_assinatura, data_termino=None, status="cancelada"):
    """Atalho: cancela (ou expira) uma assinatura ativa usando a data de hoje por padrao."""
    status = validar_opcao(status, ("cancelada", "expirada"), "status")
    termino = validar_data(data_termino or date.today(), "data de termino")
    ass = obter_assinatura(id_assinatura)
    if not ass:
        raise ErroAplicacao("Assinatura nao encontrada.")
    if ass["status"] != "ativa":
        raise ErroAplicacao("Somente assinaturas ativas podem ser encerradas.")
    if termino < ass["data_inicio"]:
        raise ErroAplicacao("A data de termino nao pode ser anterior a data de inicio.")
    executar("UPDATE assinatura SET status = %s, data_termino = %s WHERE id_assinatura = %s",
             (status, termino, id_assinatura))


def excluir_assinatura(id_assinatura):
    if not obter_assinatura(id_assinatura):
        raise ErroAplicacao("Assinatura nao encontrada.")
    executar("DELETE FROM assinatura WHERE id_assinatura = %s", (id_assinatura,))