"""Testes de rota (contrato HTTP) de autenticação e autorização.

Não usam o MySQL: os serviços são substituídos com monkeypatch, então rodam
rápido e não alteram a base de desenvolvimento (combinado do §6 do PDF).
"""
from datetime import date, datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from api import config
from api.main import app
from api.security import criar_token, decodificar_token
from services.auth_service import ConflitoErro, CredenciaisInvalidas

BASE = "/api/v1"
SENHA = "SenhaForte123!"
SEGREDO = "chave-de-teste-com-mais-de-32-caracteres"

client = TestClient(app)  # sem "with": não dispara o lifespan (validação do .env)

COMUM = {
    "id_usuario": 5, "nome": "Pessoa Comum", "email": "comum@example.com",
    "papel": "usuario", "data_cadastro": datetime(2026, 11, 20, 10, 30),
}
ADMIN = {
    "id_usuario": 1, "nome": "Admin", "email": "admin@example.com",
    "papel": "admin", "data_cadastro": datetime(2026, 11, 1, 9, 0),
}


def _assinatura(id_usuario):
    return {
        "id_assinatura": 10, "id_usuario": id_usuario, "usuario": "Fulano",
        "id_plano": 1, "plano": "Básico", "valor": 20.0,
        "data_inicio": date(2026, 11, 1), "data_termino": None, "status": "ativa",
    }


@pytest.fixture(autouse=True)
def segredo_jwt(monkeypatch):
    monkeypatch.setattr(config, "JWT_SECRET", SEGREDO)


def _como(monkeypatch, usuario):
    """Faz o servidor 'conhecer' o usuário e devolve o cabeçalho Authorization."""
    monkeypatch.setattr(
        "api.dependencies.obter_usuario_publico",
        lambda id_: usuario if id_ == usuario["id_usuario"] else None,
    )
    return {"Authorization": f"Bearer {criar_token(usuario['id_usuario'])}"}


# ---------------------------------------------------------------- login
def test_login_valido_retorna_token_e_dados_publicos(monkeypatch):
    monkeypatch.setattr("api.routers.auth.autenticar", lambda email, senha: COMUM)
    r = client.post(f"{BASE}/auth/login", json={"email": COMUM["email"], "senha": SENHA})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["token_type"] == "bearer"
    assert decodificar_token(corpo["access_token"]) == COMUM["id_usuario"]
    assert corpo["usuario"]["papel"] == "usuario"
    assert "senha_hash" not in r.text


def test_login_credenciais_invalidas_retorna_401(monkeypatch):
    def recusar(email, senha):
        raise CredenciaisInvalidas("E-mail ou senha invalidos.")

    monkeypatch.setattr("api.routers.auth.autenticar", recusar)
    r = client.post(f"{BASE}/auth/login", json={"email": COMUM["email"], "senha": "errada123"})
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_login_com_campo_extra_retorna_422():
    r = client.post(f"{BASE}/auth/login", json={"email": "a@b.com", "senha": SENHA, "papel": "admin"})
    assert r.status_code == 422


# ------------------------------------------------------------- cadastro
def test_cadastro_cria_usuario_comum(monkeypatch):
    recebido = {}

    def falso_criar_conta(**kwargs):
        recebido.update(kwargs)
        return COMUM["id_usuario"]

    monkeypatch.setattr("api.routers.auth.criar_conta", falso_criar_conta)
    monkeypatch.setattr("api.routers.auth.obter_usuario_publico", lambda id_: COMUM)
    r = client.post(
        f"{BASE}/auth/register",
        json={"nome": "Pessoa Comum", "email": COMUM["email"], "senha": SENHA, "id_plano": 1},
    )
    assert r.status_code == 201
    assert recebido["papel"] == "usuario"
    assert r.json()["papel"] == "usuario"
    assert "senha_hash" not in r.text and SENHA not in r.text


def test_cadastro_nao_aceita_papel_admin():
    r = client.post(
        f"{BASE}/auth/register",
        json={"nome": "X", "email": "x@example.com", "senha": SENHA, "id_plano": 1, "papel": "admin"},
    )
    assert r.status_code == 422


def test_cadastro_email_duplicado_retorna_409(monkeypatch):
    def duplicado(**kwargs):
        raise ConflitoErro("E-mail ja cadastrado.")

    monkeypatch.setattr("api.routers.auth.criar_conta", duplicado)
    r = client.post(
        f"{BASE}/auth/register",
        json={"nome": "X", "email": COMUM["email"], "senha": SENHA, "id_plano": 1},
    )
    assert r.status_code == 409


def test_cadastro_invalido_retorna_422_sem_ecoar_a_senha():
    r = client.post(
        f"{BASE}/auth/register",
        json={"nome": "X", "email": "x@example.com", "senha": SENHA},  # falta id_plano
    )
    assert r.status_code == 422
    assert SENHA not in r.text


# ------------------------------------------------------------------ /me
def test_me_sem_token_retorna_401():
    assert client.get(f"{BASE}/auth/me").status_code == 401


def test_me_com_esquema_errado_retorna_401():
    r = client.get(f"{BASE}/auth/me", headers={"Authorization": "Basic abc123"})
    assert r.status_code == 401


def test_me_com_token_valido(monkeypatch):
    headers = _como(monkeypatch, COMUM)
    r = client.get(f"{BASE}/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["id_usuario"] == COMUM["id_usuario"]
    assert "senha_hash" not in r.text


def test_me_com_token_expirado_retorna_401(monkeypatch):
    monkeypatch.setattr(config, "JWT_EXPIRA_MINUTOS", -5)
    headers = _como(monkeypatch, COMUM)
    assert client.get(f"{BASE}/auth/me", headers=headers).status_code == 401


def test_me_com_token_assinado_por_outra_chave_retorna_401(monkeypatch):
    _como(monkeypatch, COMUM)
    agora = datetime.now(timezone.utc)
    falso = jwt.encode(
        {"sub": "5", "iat": agora, "exp": agora + timedelta(minutes=5)},
        "outra-chave-totalmente-diferente-123456", algorithm="HS256",
    )
    r = client.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {falso}"})
    assert r.status_code == 401


def test_me_com_usuario_inexistente_retorna_401(monkeypatch):
    monkeypatch.setattr("api.dependencies.obter_usuario_publico", lambda id_: None)
    headers = {"Authorization": f"Bearer {criar_token(999)}"}
    assert client.get(f"{BASE}/auth/me", headers=headers).status_code == 401


# --------------------------------------------- rotas só de administrador
ROTAS_ADMIN = [
    ("get", f"{BASE}/usuarios", None),
    ("get", f"{BASE}/usuarios/5", None),
    ("post", f"{BASE}/usuarios",
     {"nome": "N", "email": "n@example.com", "senha": SENHA, "id_plano": 1}),
    ("delete", f"{BASE}/usuarios/9", None),
    ("get", f"{BASE}/indicadores", None),
]


@pytest.mark.parametrize("metodo,url,corpo", ROTAS_ADMIN)
def test_rota_admin_sem_token_retorna_401(metodo, url, corpo):
    r = getattr(client, metodo)(url, json=corpo) if corpo else getattr(client, metodo)(url)
    assert r.status_code == 401


@pytest.mark.parametrize("metodo,url,corpo", ROTAS_ADMIN)
def test_rota_admin_com_usuario_comum_retorna_403(monkeypatch, metodo, url, corpo):
    headers = _como(monkeypatch, COMUM)
    chamada = getattr(client, metodo)
    r = chamada(url, json=corpo, headers=headers) if corpo else chamada(url, headers=headers)
    assert r.status_code == 403


def test_admin_lista_usuarios(monkeypatch):
    headers = _como(monkeypatch, ADMIN)
    monkeypatch.setattr("api.routers.usuarios.listar_usuarios_publico", lambda busca=None: [COMUM, ADMIN])
    r = client.get(f"{BASE}/usuarios", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert "senha_hash" not in r.text


# ------------------------------- cada usuário só acessa os próprios dados
def test_assinatura_de_outro_usuario_retorna_403(monkeypatch):
    headers = _como(monkeypatch, COMUM)
    monkeypatch.setattr("services.assinatura_service.obter_assinatura", lambda id_: _assinatura(99))
    assert client.get(f"{BASE}/assinaturas/10", headers=headers).status_code == 403


def test_assinatura_propria_e_acesso_do_admin(monkeypatch):
    monkeypatch.setattr("services.assinatura_service.obter_assinatura", lambda id_: _assinatura(5))
    assert client.get(f"{BASE}/assinaturas/10", headers=_como(monkeypatch, COMUM)).status_code == 200
    monkeypatch.setattr("services.assinatura_service.obter_assinatura", lambda id_: _assinatura(99))
    assert client.get(f"{BASE}/assinaturas/10", headers=_como(monkeypatch, ADMIN)).status_code == 200


def test_listagem_de_assinaturas_filtra_pelo_usuario_logado(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "services.assinatura_service.listar_assinaturas",
        lambda id_usuario, status: chamadas.append((id_usuario, status)) or [],
    )
    client.get(f"{BASE}/assinaturas?id_usuario=99", headers=_como(monkeypatch, COMUM))
    client.get(f"{BASE}/assinaturas?id_usuario=99", headers=_como(monkeypatch, ADMIN))
    assert chamadas == [(5, None), (99, None)]  # comum: forçado ao próprio id; admin: pode filtrar


def test_listagem_de_historico_filtra_pelo_usuario_logado(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "services.historico_service.listar_historico",
        lambda id_usuario, limite: chamadas.append((id_usuario, limite)) or [],
    )
    client.get(f"{BASE}/historico?id_usuario=99", headers=_como(monkeypatch, COMUM))
    client.get(f"{BASE}/historico?id_usuario=99", headers=_como(monkeypatch, ADMIN))
    assert chamadas == [(5, 200), (99, 200)]


def test_usuario_comum_nao_registra_historico_de_outro(monkeypatch):
    headers = _como(monkeypatch, COMUM)

    def nao_deve_chamar(*args, **kwargs):
        raise AssertionError("o serviço não deveria ser chamado")

    monkeypatch.setattr("services.historico_service.registrar_reproducao", nao_deve_chamar)
    r = client.post(
        f"{BASE}/historico",
        json={"id_usuario": 99, "id_conteudo": 1, "progresso_minutos": 10},
        headers=headers,
    )
    assert r.status_code == 403


def test_exclusao_de_historico_de_outro_usuario(monkeypatch):
    monkeypatch.setattr(
        "api.routers.historico.obter_reproducao",
        lambda id_: {"id_reproducao": id_, "id_usuario": 99},
    )
    excluidos = []
    monkeypatch.setattr("services.historico_service.excluir_reproducao", excluidos.append)

    assert client.delete(f"{BASE}/historico/1", headers=_como(monkeypatch, COMUM)).status_code == 403
    assert excluidos == []
    assert client.delete(f"{BASE}/historico/1", headers=_como(monkeypatch, ADMIN)).status_code == 204
    assert excluidos == [1]