"""Autenticação e contas (senha_hash + papel).

Arquivo NOVO: não altera o usuario_service.py existente. Aqui ficam as operações
que dependem das colunas senha_hash/papel, que o usuario_service não conhece.
"""
import bcrypt

from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import exigir_texto, validar_email, validar_opcao

PAPEIS = ("admin", "usuario")
_PUBLICAS = "id_usuario, nome, email, papel, data_cadastro"

# Hash descartável: gasta o mesmo tempo no login mesmo quando o e-mail não existe.
_HASH_FALSO = bcrypt.hashpw(b"senha-falsa", bcrypt.gensalt())


class ConflitoErro(ErroAplicacao):
    """Conflito de dados (ex.: e-mail já cadastrado) -> HTTP 409."""


class CredenciaisInvalidas(ErroAplicacao):
    """Login inválido -> HTTP 401."""


# ---------- senhas ----------
def validar_senha(senha):
    if not isinstance(senha, str) or len(senha) < 8:
        raise ErroAplicacao("A senha deve ter no mínimo 8 caracteres.")
    if len(senha.encode("utf-8")) > 72:
        raise ErroAplicacao("A senha deve ter no máximo 72 bytes.")
    return senha


def gerar_hash(senha):
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _conferir(senha, hash_armazenado):
    try:
        return bcrypt.checkpw(senha.encode("utf-8")[:72], hash_armazenado)
    except (ValueError, TypeError):
        return False


# ---------- consultas ----------
def obter_por_email(email):
    """Uso INTERNO (inclui senha_hash). Nunca retornar este dict pela API."""
    r = consultar(
        "SELECT id_usuario, nome, email, senha_hash, papel, data_cadastro "
        "FROM usuario WHERE email = %s", (email,))
    return r[0] if r else None


def obter_usuario_publico(id_usuario):
    r = consultar(f"SELECT {_PUBLICAS} FROM usuario WHERE id_usuario = %s", (id_usuario,))
    return r[0] if r else None


def listar_usuarios_publico(busca=None):
    if busca and busca.strip():
        like = f"%{busca.strip()}%"
        return consultar(
            f"SELECT {_PUBLICAS} FROM usuario WHERE nome LIKE %s OR email LIKE %s ORDER BY nome",
            (like, like))
    return consultar(f"SELECT {_PUBLICAS} FROM usuario ORDER BY nome")


# ---------- login / contas ----------
def autenticar(email, senha):
    email = (email or "").strip().lower()
    usuario = obter_por_email(email)
    hash_db = usuario["senha_hash"] if usuario and usuario.get("senha_hash") else None
    if isinstance(hash_db, str):
        hash_db = hash_db.encode("utf-8")
    ok = _conferir(senha or "", hash_db or _HASH_FALSO)
    if not usuario or not hash_db or not ok:
        raise CredenciaisInvalidas("E-mail ou senha inválidos.")
    return obter_usuario_publico(usuario["id_usuario"])


def criar_conta(nome, email, senha, papel="usuario"):
    nome = exigir_texto(nome, "nome", 120)
    email = validar_email(email)
    senha = validar_senha(senha)
    papel = validar_opcao(papel, PAPEIS, "papel")
    if obter_por_email(email):
        raise ConflitoErro("E-mail já cadastrado.")
    return executar(
        "INSERT INTO usuario (nome, email, senha_hash, papel) VALUES (%s, %s, %s, %s)",
        (nome, email, gerar_hash(senha), papel))


def definir_senha(id_usuario, senha):
    senha = validar_senha(senha)
    executar("UPDATE usuario SET senha_hash = %s WHERE id_usuario = %s",
             (gerar_hash(senha), id_usuario))


def definir_papel(id_usuario, papel):
    papel = validar_opcao(papel, PAPEIS, "papel")
    executar("UPDATE usuario SET papel = %s WHERE id_usuario = %s", (papel, id_usuario))
