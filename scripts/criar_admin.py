"""Procedimento seguro de inicialização do 1º administrador.

Uso (na raiz do projeto):
    python -m scripts.criar_admin

Lê ADMIN_NOME / ADMIN_EMAIL / ADMIN_SENHA do ambiente ou pergunta no terminal
(a senha é digitada sem eco e nunca é impressa).
Se o e-mail já existir, promove a conta a admin e redefine a senha.
"""
import getpass
import os

from dotenv import load_dotenv

load_dotenv()

from services.auth_service import (criar_conta, definir_papel, definir_senha,  # noqa: E402
                                   obter_por_email)


def main():
    nome = os.getenv("ADMIN_NOME") or input("Nome: ")
    email = (os.getenv("ADMIN_EMAIL") or input("E-mail: ")).strip().lower()
    senha = os.getenv("ADMIN_SENHA") or getpass.getpass("Senha (mín. 8 caracteres): ")

    existente = obter_por_email(email)
    if existente:
        definir_senha(existente["id_usuario"], senha)
        definir_papel(existente["id_usuario"], "admin")
        print(f"Conta existente promovida a admin: {email}")
    else:
        criar_conta(nome, email, senha, papel="admin")
        print(f"Administrador criado: {email}")


if __name__ == "__main__":
    main()
