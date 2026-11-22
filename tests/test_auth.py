import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from api.schemas import RegistroIn
from api.security import criar_token, decodificar_token
from api.dependencies import eh_admin
from services.auth_service import (
    gerar_hash,
    _conferir,
    validar_senha,
)
from database.erros import ErroAplicacao


def test_hash_senha():
    senha = "SenhaForte123!"

    hash_gerado = gerar_hash(senha)

    assert hash_gerado != senha
    assert hash_gerado.startswith("$2")
    assert _conferir(
        senha,
        hash_gerado.encode("utf-8")
    )


def test_senha_incorreta():
    hash_gerado = gerar_hash("SenhaCorreta123!")

    assert not _conferir(
        "SenhaErrada123!",
        hash_gerado.encode("utf-8")
    )


def test_senha_curta():
    with pytest.raises(ErroAplicacao):
        validar_senha("123")


def test_cadastro_exige_plano():
    with pytest.raises(ValidationError):
        RegistroIn(
            nome="Usuario Teste",
            email="teste@email.com",
            senha="SenhaForte123!"
        )


def test_cadastro_nao_permite_admin():
    with pytest.raises(ValidationError):
        RegistroIn(
            nome="Usuario Teste",
            email="teste@email.com",
            senha="SenhaForte123!",
            id_plano=1,
            papel="admin"
        )


def test_cadastro_valido():
    dados = RegistroIn(
        nome="Usuario Teste",
        email="teste@email.com",
        senha="SenhaForte123!",
        id_plano=1
    )

    assert dados.id_plano == 1


def test_permissao_admin():
    assert eh_admin({"papel": "admin"})
    assert not eh_admin({"papel": "usuario"})


def test_jwt(monkeypatch):
    from api import config

    monkeypatch.setattr(
        config,
        "JWT_SECRET",
        "chave-de-teste-com-mais-de-32-caracteres"
    )

    token = criar_token(10)

    assert decodificar_token(token) == 10


def test_jwt_invalido(monkeypatch):
    from api import config

    monkeypatch.setattr(
        config,
        "JWT_SECRET",
        "chave-de-teste-com-mais-de-32-caracteres"
    )

    with pytest.raises(HTTPException) as erro:
        decodificar_token("token.invalido.aqui")

    assert erro.value.status_code == 401