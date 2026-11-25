
from copy import deepcopy
from datetime import date, timedelta

from mocks.dados_mock import PLANOS
from mocks.usuarios_mock import listar_usuarios


# Dados iniciais para simular assinaturas cadastradas.
ASSINATURAS = [
    {
        "id_assinatura": 1,
        "id_usuario": 2,
        "usuario": "Usuário de Teste",
        "id_plano": 2,
        "plano": "padrao",
        "valor": 35.00,
        "data_inicio": date.today() - timedelta(days=15),
        "data_termino": None,
        "status": "ativa"
    }
]


def listar_planos():
    """Retorna todos os planos disponíveis."""
    return deepcopy(PLANOS)


def listar_assinaturas(status=None):
    """Retorna as assinaturas, permitindo filtrar pelo status."""

    usuarios = {
        u["id_usuario"]: u
        for u in listar_usuarios()
    }

    resultado = []

    for assinatura in ASSINATURAS:
        if status and assinatura["status"] != status:
            continue

        dados = deepcopy(assinatura)

        usuario = usuarios.get(dados["id_usuario"])

        if usuario:
            dados["usuario"] = usuario["nome"]

        plano = next(
            (
                p for p in PLANOS
                if p["id_plano"] == dados["id_plano"]
            ),
            None
        )

        if plano:
            dados["plano"] = plano["nome"]

        resultado.append(dados)

    return resultado


def criar_assinatura(
    id_usuario,
    id_plano,
    data_inicio,
    data_termino,
    status,
    valor=None
):
    """Cadastra uma nova assinatura."""

    usuarios = listar_usuarios()

    usuario = next(
        (u for u in usuarios if u["id_usuario"] == id_usuario),
        None
    )

    if usuario is None:
        raise ValueError("Usuário não encontrado.")

    plano = next(
        (p for p in PLANOS if p["id_plano"] == id_plano),
        None
    )

    if plano is None:
        raise ValueError("Plano não encontrado.")

    if status not in ("ativa", "cancelada", "expirada"):
        raise ValueError("Status de assinatura inválido.")

    if status == "ativa":
        data_termino = None
    elif data_termino is None or data_termino < data_inicio:
        raise ValueError("Data de término inválida.")

    novo_id = max(
        (a["id_assinatura"] for a in ASSINATURAS),
        default=0
    ) + 1

    nova_assinatura = {
        "id_assinatura": novo_id,
        "id_usuario": id_usuario,
        "usuario": usuario["nome"],
        "id_plano": id_plano,
        "plano": plano["nome"],
        "valor": float(valor if valor is not None else plano["valor"]),
        "data_inicio": data_inicio,
        "data_termino": data_termino,
        "status": status
    }

    ASSINATURAS.append(nova_assinatura)

    return deepcopy(nova_assinatura)


def atualizar_assinatura(
    id_assinatura,
    id_usuario,
    id_plano,
    data_inicio,
    data_termino,
    status,
    valor
):
    """Atualiza os dados de uma assinatura."""

    assinatura = next(
        (
            a for a in ASSINATURAS
            if a["id_assinatura"] == id_assinatura
        ),
        None
    )

    if assinatura is None:
        raise ValueError("Assinatura não encontrada.")

    usuario = next(
        (
            u for u in listar_usuarios()
            if u["id_usuario"] == id_usuario
        ),
        None
    )

    if usuario is None:
        raise ValueError("Usuário não encontrado.")

    plano = next(
        (p for p in PLANOS if p["id_plano"] == id_plano),
        None
    )

    if plano is None:
        raise ValueError("Plano não encontrado.")

    assinatura["id_usuario"] = id_usuario
    assinatura["usuario"] = usuario["nome"]
    assinatura["id_plano"] = id_plano
    assinatura["plano"] = plano["nome"]
    assinatura["data_inicio"] = data_inicio
    assinatura["data_termino"] = data_termino
    assinatura["status"] = status
    assinatura["valor"] = float(valor)

    return deepcopy(assinatura)


def encerrar_assinatura(id_assinatura, data_termino, status):
    """Encerra uma assinatura ativa."""

    assinatura = next(
        (
            a for a in ASSINATURAS
            if a["id_assinatura"] == id_assinatura
        ),
        None
    )

    if assinatura is None:
        raise ValueError("Assinatura não encontrada.")

    if assinatura["status"] != "ativa":
        raise ValueError("A assinatura não está ativa.")

    if status not in ("cancelada", "expirada"):
        raise ValueError("Status de encerramento inválido.")

    if data_termino < assinatura["data_inicio"]:
        raise ValueError("Data de término inválida.")

    assinatura["status"] = status
    assinatura["data_termino"] = data_termino


def excluir_assinatura(id_assinatura):
    """Exclui uma assinatura."""

    assinatura = next(
        (
            a for a in ASSINATURAS
            if a["id_assinatura"] == id_assinatura
        ),
        None
    )

    if assinatura is None:
        raise ValueError("Assinatura não encontrada.")

    ASSINATURAS.remove(assinatura)
