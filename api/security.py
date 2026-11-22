"""Geração e validação de tokens JWT."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException

from api import config

_HEADERS_401 = {"WWW-Authenticate": "Bearer"}


def criar_token(id_usuario: int) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(id_usuario),
        "iat": agora,
        "exp": agora + timedelta(minutes=config.JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decodificar_token(token: str) -> int:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Token inválido ou expirado.", headers=_HEADERS_401)
