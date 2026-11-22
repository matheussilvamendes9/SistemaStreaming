"""StreamHub API.  Execute na raiz do projeto:

    uvicorn api.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import config
from api.errors import registrar_handlers
from api.routers import (assinaturas, auth, catalogo, historico, indicadores,
                         planos, usuarios)

PREFIXO = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validar_configuracao()
    yield


app = FastAPI(title="StreamHub API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
registrar_handlers(app)

for modulo in (auth, usuarios, catalogo, planos, assinaturas, historico, indicadores):
    for roteador in modulo.ROTEADORES:
        app.include_router(roteador, prefix=PREFIXO)


@app.get("/health", tags=["Infra"])
def health():
    return {"status": "ok"}
