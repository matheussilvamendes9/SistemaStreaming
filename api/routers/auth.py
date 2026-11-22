from fastapi import APIRouter, Depends

from api.dependencies import usuario_atual
from api.schemas import LoginIn, RegistroIn, TokenOut, UsuarioOut
from api.security import criar_token
from services.auth_service import (
    autenticar,
    criar_conta,
    obter_usuario_publico,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenOut)
def login(dados: LoginIn):
    usuario = autenticar(dados.email, dados.senha)

    return {
        "access_token": criar_token(usuario["id_usuario"]),
        "token_type": "bearer",
        "usuario": usuario,
    }


@router.post(
    "/register",
    response_model=UsuarioOut,
    status_code=201,
)
def register(dados: RegistroIn):

    id_usuario = criar_conta(
        nome=dados.nome,
        email=dados.email,
        senha=dados.senha,
        papel="usuario",
        id_plano=dados.id_plano,
    )

    return obter_usuario_publico(id_usuario)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: dict = Depends(usuario_atual)):
    return usuario


ROTEADORES = [router]