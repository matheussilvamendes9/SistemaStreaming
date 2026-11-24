
from copy import deepcopy

from mocks.dados_mock import USUARIO_ADMIN, USUARIO_COMUM


# Dados iniciais para simular os usuários cadastrados.
USUARIOS = [
    deepcopy(USUARIO_ADMIN),
    deepcopy(USUARIO_COMUM),
]


def listar_usuarios():
    """Retorna todos os usuários cadastrados."""
    return deepcopy(USUARIOS)


def criar_usuario(nome, email):
    """Cadastra um novo usuário."""

    nome = nome.strip()
    email = email.strip().lower()

    if not nome or not email:
        raise ValueError("Preencha todos os campos.")

    if "@" not in email:
        raise ValueError("Informe um e-mail válido.")

    if any(u["email"].lower() == email for u in USUARIOS):
        raise ValueError("Já existe um usuário com esse e-mail.")

    novo_id = max(
        (u["id_usuario"] for u in USUARIOS),
        default=0
    ) + 1

    novo_usuario = {
        "id_usuario": novo_id,
        "nome": nome,
        "email": email,
        "papel": "usuario"
    }

    USUARIOS.append(novo_usuario)

    return deepcopy(novo_usuario)


def atualizar_usuario(id_usuario, nome, email):
    """Atualiza os dados de um usuário."""

    nome = nome.strip()
    email = email.strip().lower()

    if not nome or not email:
        raise ValueError("Preencha todos os campos.")

    if "@" not in email:
        raise ValueError("Informe um e-mail válido.")

    usuario = next(
        (u for u in USUARIOS if u["id_usuario"] == id_usuario),
        None
    )

    if usuario is None:
        raise ValueError("Usuário não encontrado.")

    email_duplicado = any(
        u["email"].lower() == email
        and u["id_usuario"] != id_usuario
        for u in USUARIOS
    )

    if email_duplicado:
        raise ValueError("Já existe outro usuário com esse e-mail.")

    usuario["nome"] = nome
    usuario["email"] = email

    return deepcopy(usuario)


def excluir_usuario(id_usuario):
    """Exclui um usuário."""

    usuario = next(
        (u for u in USUARIOS if u["id_usuario"] == id_usuario),
        None
    )

    if usuario is None:
        raise ValueError("Usuário não encontrado.")

    USUARIOS.remove(usuario)
