from fastapi import APIRouter, Depends

from api.dependencies import usuario_atual
from api.schemas import PlanoOut
from services import plano_service

router = APIRouter(prefix="/planos", tags=["Planos"])


@router.get("", response_model=list[PlanoOut])
def listar(_: dict = Depends(usuario_atual)):
    return plano_service.listar_planos()


ROTEADORES = [router]
