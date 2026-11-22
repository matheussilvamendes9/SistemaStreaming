"""Tradução de exceções dos serviços para os códigos HTTP do contrato."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from database.erros import ErroAplicacao
from services.auth_service import ConflitoErro, CredenciaisInvalidas

log = logging.getLogger("streamhub.api")

_TERMOS_CONFLITO = ("ja existe", "ja cadastrad", "duplicad", "ja possui", "ja tem")


def _resp(status, detail, headers=None):
    return JSONResponse(status_code=status, content={"detail": detail}, headers=headers)


async def tratar_erro_aplicacao(request: Request, exc: ErroAplicacao):
    msg = str(exc) or "Requisição inválida."
    baixa = msg.lower()
    if isinstance(exc, CredenciaisInvalidas):
        return _resp(401, msg, {"WWW-Authenticate": "Bearer"})
    if isinstance(exc, ConflitoErro) or any(t in baixa for t in _TERMOS_CONFLITO):
        return _resp(409, msg)
    if "nao encontrad" in baixa or "não encontrad" in baixa:
        return _resp(404, msg)
    return _resp(400, msg)


async def tratar_validacao(request: Request, exc: RequestValidationError):
    # Não devolve "input": evitaria ecoar senhas enviadas pelo cliente.
    detalhes = [
        {
            "campo": ".".join(str(p) for p in e["loc"] if p != "body"),
            "mensagem": e["msg"],
        }
        for e in exc.errors()
    ]
    return _resp(422, detalhes)


async def tratar_inesperado(request: Request, exc: Exception):
    if type(exc).__name__ == "IntegrityError":
        return _resp(409, "A operação viola uma restrição de integridade dos dados.")
    log.exception("Erro inesperado em %s %s", request.method, request.url.path)
    return _resp(500, "Erro interno inesperado.")


def registrar_handlers(app: FastAPI):
    app.add_exception_handler(ErroAplicacao, tratar_erro_aplicacao)
    app.add_exception_handler(RequestValidationError, tratar_validacao)
    app.add_exception_handler(Exception, tratar_inesperado)
