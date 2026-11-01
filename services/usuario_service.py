"""RF01 - CRUD de usuarios."""
from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import exigir_texto, validar_email

_COLUNAS = "id_usuario, nome, email, data_cadastro"


def listar_usuarios(busca=None):
    if busca and busca.strip():
        like = f"%{busca.strip()}%"
        return consultar(
            f"SELECT {_COLUNAS} FROM usuario WHERE nome LIKE %s OR email LIKE %s ORDER BY nome",
            (like, like),
        )
    return consultar(f"SELECT {_COLUNAS} FROM usuario ORDER BY nome")


def obter_usuario(id_usuario):
    r = consultar(f"SELECT {_COLUNAS} FROM usuario WHERE id_usuario = %s", (id_usuario,))
    return r[0] if r else None


def criar_usuario(nome, email):
    nome = exigir_texto(nome, "nome", 100)
    email = validar_email(email)
    return executar("INSERT INTO usuario (nome, email) VALUES (%s, %s)", (nome, email))


def atualizar_usuario(id_usuario, nome, email):
    nome = exigir_texto(nome, "nome", 100)
    email = validar_email(email)
    executar("UPDATE usuario SET nome = %s, email = %s WHERE id_usuario = %s",
             (nome, email, id_usuario))


def excluir_usuario(id_usuario):
    if not obter_usuario(id_usuario):
        raise ErroAplicacao("Usuario nao encontrado.")
    executar("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))