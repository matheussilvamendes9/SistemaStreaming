
from mocks.dados_mock import USUARIO_ADMIN, USUARIO_COMUM


# Credenciais fictícias, utilizadas somente durante o desenvolvimento.
USUARIOS_TESTE = {
    "admin@streamhub.com": {
        "senha": "admin123",
        "usuario": USUARIO_ADMIN
    },
    "usuario@streamhub.com": {
        "senha": "usuario123",
        "usuario": USUARIO_COMUM
    }
}


def fazer_login(email, senha):
    """
    Simula a autenticação de um usuário.
    """

    usuario_teste = USUARIOS_TESTE.get(email)

    if usuario_teste is None:
        raise ValueError("E-mail ou senha incorretos.")

    if usuario_teste["senha"] != senha:
        raise ValueError("E-mail ou senha incorretos.")

    return {
        "access_token": "token_mock_streamhub",
        "token_type": "bearer",
        "usuario": usuario_teste["usuario"]
    }


def obter_usuario_atual(token):
    """
    Simula a identificação do usuário autenticado.
    """

    if token != "token_mock_streamhub":
        raise ValueError("Sessão inválida ou expirada.")

    # Neste mock, o administrador é apenas um usuário de teste.
    # A identificação real será feita pela API.
    return None
