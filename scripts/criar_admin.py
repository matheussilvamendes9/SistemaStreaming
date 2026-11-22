"""Procedimento seguro de inicialização do 1º administrador.

Uso (na raiz do projeto):
    python -m scripts.criar_admin

Lê ADMIN_NOME / ADMIN_EMAIL / ADMIN_SENHA do ambiente ou pergunta no terminal
(a senha é digitada sem eco e nunca é impressa).
Se o e-mail já existir, promove a conta a admin e redefine a senha.

O administrador é criado SEM assinatura: o plano só é exigido no cadastro de
usuários comuns (criar_conta), por isso este script grava a conta diretamente.
"""
import getpass
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from database.connection import executar  # noqa: E402
from database.erros import ErroAplicacao  # noqa: E402
from services.auth_service import (  # noqa: E402
    definir_papel,
    definir_senha,
    gerar_hash,
    obter_por_email,
    validar_senha,
)
from services.validators import exigir_texto, validar_email  # noqa: E402


def _ler_senha():
    senha = os.getenv("ADMIN_SENHA")
    if senha:
        return senha
    senha = getpass.getpass("Senha (mín. 8 caracteres): ")
    if senha != getpass.getpass("Confirme a senha: "):
        raise ErroAplicacao("As senhas informadas não conferem.")
    return senha


def _criar_admin(nome, email, senha):
    """Insere o administrador diretamente (sem assinatura inicial)."""
    return executar(
        "INSERT INTO usuario (nome, email, senha_hash, papel) "
        "VALUES (%s, %s, %s, 'admin')",
        (nome, email, gerar_hash(senha)),
    )


def main():
    nome = exigir_texto(os.getenv("ADMIN_NOME") or input("Nome: "), "nome", 120)
    email = validar_email(os.getenv("ADMIN_EMAIL") or input("E-mail: "))
    senha = validar_senha(_ler_senha())

    existente = obter_por_email(email)
    if existente:
        definir_senha(existente["id_usuario"], senha)
        definir_papel(existente["id_usuario"], "admin")
        print(f"Conta existente promovida a admin: {email}")
    else:
        _criar_admin(nome, email, senha)
        print(f"Administrador criado: {email}")


if __name__ == "__main__":
    try:
        main()
    except ErroAplicacao as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        sys.exit(1)