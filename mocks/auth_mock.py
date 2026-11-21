
from mocks.dados_mock import USUARIO_ADMIN, USUARIO_COMUM


# Credenciais fictícias para desenvolvimento.
USUARIOS_TESTE = {
    "admin@streamhub.com": {
        "senha": "admin123",
        "usuario": USUARIO_ADMIN,
        "token": "token_mock_admin"
    },
    "usuario@streamhub.com": {
        "senha": "usuario123",
        "usuario": USUARIO_COMUM,
        "token": "token_mock_usuario"
    }
}


def fazer_login(email, senha):
    """
    Simula a autenticação de um usuário.
    """

    usuario_teste = USUARIOS_TESTE.get(email)

    if usuario_teste is None or usuario_teste["senha"] != senha:
        raise ValueError("E-mail ou senha incorretos.")

    return {
        "access_token": usuario_teste["token"],
        "token_type": "bearer",
        "usuario": usuario_teste["usuario"]
    }


def obter_usuario_atual(token):
    """
    Identifica o usuário associado ao token fictício.
    """

    for usuario_teste in USUARIOS_TESTE.values():
        if usuario_teste["token"] == token:
            return usuario_teste["usuario"]

    raise ValueError("Sessão inválida ou expirada.")
