"""Dependências de autenticação/autorização (a permissão real é validada aqui)."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.security import decodificar_token
from services.auth_service import obter_usuario_publico

_bearer = HTTPBearer(auto_error=False)
_HEADERS_401 = {"WWW-Authenticate": "Bearer"}


def usuario_atual(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if cred is None:
        raise HTTPException(401, "Não autenticado.", headers=_HEADERS_401)
    id_usuario = decodificar_token(cred.credentials)
    # Busca no banco a cada requisição: papel e existência sempre atualizados.
    usuario = obter_usuario_publico(id_usuario)
    if not usuario:
        raise HTTPException(401, "Usuário do token não existe mais.", headers=_HEADERS_401)
    return usuario


def exigir_admin(usuario: dict = Depends(usuario_atual)) -> dict:
    if usuario["papel"] != "admin":
        raise HTTPException(403, "Acesso restrito a administradores.")
    return usuario


def eh_admin(usuario: dict) -> bool:
    return usuario["papel"] == "admin"
