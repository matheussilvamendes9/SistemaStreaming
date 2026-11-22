"""Autenticacao, cadastro de contas e seguranca de senhas."""

from datetime import date
from decimal import Decimal

import bcrypt

from database.connection import consultar, executar, transacao
from database.erros import ErroAplicacao
from services.validators import (
    exigir_texto,
    validar_email,
    validar_inteiro,
    validar_opcao,
)

PAPEIS = ("admin", "usuario")

_PUBLICAS = (
    "id_usuario, nome, email, papel, data_cadastro"
)

# Hash usado para evitar diferencas evidentes no tempo de login
# entre emails existentes e inexistentes.
_HASH_FALSO = bcrypt.hashpw(
    b"senha-falsa",
    bcrypt.gensalt()
)


class ConflitoErro(ErroAplicacao):
    """Conflito de dados, como email duplicado."""


class CredenciaisInvalidas(ErroAplicacao):
    """Credenciais incorretas."""


# ---------- Senhas ----------

def validar_senha(senha):
    if not isinstance(senha, str) or len(senha) < 8:
        raise ErroAplicacao(
            "A senha deve ter no minimo 8 caracteres."
        )

    if len(senha.encode("utf-8")) > 72:
        raise ErroAplicacao(
            "A senha deve ter no maximo 72 bytes."
        )

    return senha


def gerar_hash(senha):
    senha = validar_senha(senha)

    return bcrypt.hashpw(
        senha.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def _conferir(senha, hash_armazenado):
    try:
        if not isinstance(senha, str):
            return False

        senha_bytes = senha.encode("utf-8")

        if len(senha_bytes) > 72:
            return False

        if isinstance(hash_armazenado, str):
            hash_armazenado = hash_armazenado.encode("utf-8")

        return bcrypt.checkpw(
            senha_bytes,
            hash_armazenado
        )

    except (ValueError, TypeError, AttributeError):
        return False

# ---------- Consultas ----------

def obter_por_email(email):
    """Consulta interna. Inclui senha_hash."""

    resultado = consultar(
        """
        SELECT
            id_usuario,
            nome,
            email,
            senha_hash,
            papel,
            data_cadastro
        FROM usuario
        WHERE email = %s
        """,
        (email,)
    )

    return resultado[0] if resultado else None


def obter_usuario_publico(id_usuario):
    resultado = consultar(
        f"""
        SELECT {_PUBLICAS}
        FROM usuario
        WHERE id_usuario = %s
        """,
        (id_usuario,)
    )

    return resultado[0] if resultado else None


def listar_usuarios_publico(busca=None):
    if busca and busca.strip():
        like = f"%{busca.strip()}%"

        return consultar(
            f"""
            SELECT {_PUBLICAS}
            FROM usuario
            WHERE nome LIKE %s OR email LIKE %s
            ORDER BY nome
            """,
            (like, like)
        )

    return consultar(
        f"SELECT {_PUBLICAS} FROM usuario ORDER BY nome"
    )


# ---------- Login ----------

def autenticar(email, senha):
    email = (email or "").strip().lower()

    usuario = obter_por_email(email)

    hash_db = (
        usuario["senha_hash"]
        if usuario and usuario.get("senha_hash")
        else None
    )

    if isinstance(hash_db, str):
        hash_db = hash_db.encode("utf-8")

    valido = _conferir(
        senha or "",
        hash_db or _HASH_FALSO
    )

    if not usuario or not hash_db or not valido:
        raise CredenciaisInvalidas(
            "E-mail ou senha invalidos."
        )

    return obter_usuario_publico(
        usuario["id_usuario"]
    )


# ---------- Cadastro com assinatura inicial ----------

def criar_conta(nome, email, senha, papel="usuario",
                id_plano=None):

    nome = exigir_texto(nome, "nome", 120)
    email = validar_email(email)
    senha = validar_senha(senha)
    papel = validar_opcao(papel, PAPEIS, "papel")

    if id_plano is None:
        raise ErroAplicacao(
            "E obrigatorio escolher um plano."
        )

    id_plano = validar_inteiro(
        id_plano, "plano", 1
    )

    senha_hash = gerar_hash(senha)

    # Usuario e assinatura sao criados na mesma transacao.
    with transacao() as cursor:

        # Confere o plano e consulta seu valor atual.
        cursor.execute(
            """
            SELECT id_plano, valor
            FROM plano
            WHERE id_plano = %s
            """,
            (id_plano,)
        )

        plano = cursor.fetchone()

        if not plano:
            raise ErroAplicacao(
                "Plano selecionado nao encontrado."
            )

        valor = Decimal(str(plano["valor"]))

        if valor <= 0:
            raise ErroAplicacao(
                "O plano deve possuir valor positivo."
            )

        # Verifica se o email ja existe.
        cursor.execute(
            """
            SELECT id_usuario
            FROM usuario
            WHERE email = %s
            """,
            (email,)
        )

        if cursor.fetchone():
            raise ConflitoErro(
                "E-mail ja cadastrado."
            )

        # Cria o usuario.
        cursor.execute(
            """
            INSERT INTO usuario
                (nome, email, senha_hash, papel)
            VALUES (%s, %s, %s, %s)
            """,
            (nome, email, senha_hash, papel)
        )

        id_usuario = cursor.lastrowid

        # Cria a assinatura inicial ativa.
        cursor.execute(
            """
            INSERT INTO assinatura
                (
                    id_usuario,
                    id_plano,
                    valor,
                    data_inicio,
                    data_termino,
                    status
                )
            VALUES (%s, %s, %s, %s, NULL, 'ativa')
            """,
            (
                id_usuario,
                id_plano,
                valor,
                date.today()
            )
        )

    return id_usuario


# ---------- Administracao de contas ----------

def definir_senha(id_usuario, senha):
    senha_hash = gerar_hash(senha)

    executar(
        """
        UPDATE usuario
        SET senha_hash = %s
        WHERE id_usuario = %s
        """,
        (senha_hash, id_usuario)
    )


def definir_papel(id_usuario, papel):
    papel = validar_opcao(
        papel, PAPEIS, "papel"
    )

    executar(
        """
        UPDATE usuario
        SET papel = %s
        WHERE id_usuario = %s
        """,
        (papel, id_usuario)
    )