from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from api.dependencies import eh_admin, usuario_atual
from api.schemas import HistoricoIn, HistoricoOut, ReproducaoCriadaOut
from services import historico_service
from services.acesso_service import obter_reproducao

router = APIRouter(prefix="/historico", tags=["Histórico"])


@router.get("", response_model=list[HistoricoOut])
def listar(id_usuario: Optional[int] = None,
           limite: int = Query(200, ge=1, le=1000),
           usuario: dict = Depends(usuario_atual)):
    if not eh_admin(usuario):
        id_usuario = usuario["id_usuario"]  # usuário comum: apenas o próprio
    return historico_service.listar_historico(id_usuario, limite)


@router.post("", response_model=ReproducaoCriadaOut, status_code=201)
def registrar(dados: HistoricoIn, usuario: dict = Depends(usuario_atual)):
    if eh_admin(usuario):
        alvo = dados.id_usuario or usuario["id_usuario"]
    else:
        if dados.id_usuario not in (None, usuario["id_usuario"]):
            raise HTTPException(403, "Você só pode registrar reproduções para si mesmo.")
        alvo = usuario["id_usuario"]
    id_reproducao = historico_service.registrar_reproducao(
        alvo, dados.id_conteudo, dados.progresso_minutos,
        dados.id_episodio, dados.data_hora)
    return {"id_reproducao": id_reproducao}


@router.delete("/{id_reproducao}", status_code=204, response_class=Response)
def excluir(id_reproducao: int, usuario: dict = Depends(usuario_atual)):
    registro = obter_reproducao(id_reproducao)
    if not registro:
        raise HTTPException(404, "Registro não encontrado.")
    if not eh_admin(usuario) and registro["id_usuario"] != usuario["id_usuario"]:
        raise HTTPException(403, "Você não tem permissão para excluir este registro.")
    historico_service.excluir_reproducao(id_reproducao)
    return Response(status_code=204)


ROTEADORES = [router]
