from fastapi import APIRouter, Depends, Query

from api.dependencies import exigir_admin
from api.schemas import IndicadoresOut
from services import indicadores_service

router = APIRouter(prefix="/indicadores", tags=["Indicadores (admin)"])


@router.get("", response_model=IndicadoresOut)
def indicadores(limite_top: int = Query(5, ge=1, le=50), _: dict = Depends(exigir_admin)):
    return indicadores_service.obter_indicadores(limite_top)


ROTEADORES = [router]
