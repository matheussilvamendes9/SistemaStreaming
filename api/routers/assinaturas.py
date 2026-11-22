from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import eh_admin, usuario_atual
from api.schemas import (AssinaturaIn, AssinaturaOut, CancelarIn,
                         StatusAssinatura)
from services import assinatura_service
from services.auth_service import obter_usuario_publico

router = APIRouter(prefix="/assinaturas", tags=["Assinaturas"])

_SO_ADMIN = "Somente administradores podem definir status, data de término, valor ou outro usuário."


def _ou_404(id_assinatura):
    ass = assinatura_service.obter_assinatura(id_assinatura)
    if not ass:
        raise HTTPException(404, "Assinatura não encontrada.")
    return ass


def _checar_dono(usuario, ass):
    if not eh_admin(usuario) and ass["id_usuario"] != usuario["id_usuario"]:
        raise HTTPException(403, "Você não tem permissão para acessar esta assinatura.")


@router.get("", response_model=list[AssinaturaOut])
def listar(status: Optional[StatusAssinatura] = None,
           id_usuario: Optional[int] = None,
           usuario: dict = Depends(usuario_atual)):
    if not eh_admin(usuario):
        id_usuario = usuario["id_usuario"]  # usuário comum só enxerga as próprias
    return assinatura_service.listar_assinaturas(id_usuario, status)


@router.get("/{id_assinatura}", response_model=AssinaturaOut)
def consultar(id_assinatura: int, usuario: dict = Depends(usuario_atual)):
    ass = _ou_404(id_assinatura)
    _checar_dono(usuario, ass)
    return ass


@router.post("", response_model=AssinaturaOut, status_code=201)
def criar(dados: AssinaturaIn, usuario: dict = Depends(usuario_atual)):
    if eh_admin(usuario):
        if dados.id_usuario is None:
            raise HTTPException(400, "Informe o id_usuario da assinatura.")
        alvo, status = dados.id_usuario, dados.status or "ativa"
        termino, valor = dados.data_termino, dados.valor
    else:
        if (dados.id_usuario not in (None, usuario["id_usuario"])
                or dados.status not in (None, "ativa")
                or dados.data_termino is not None or dados.valor is not None):
            raise HTTPException(403, _SO_ADMIN)
        alvo, status, termino, valor = usuario["id_usuario"], "ativa", None, None

    if not obter_usuario_publico(alvo):
        raise HTTPException(404, "Usuário não encontrado.")
    id_assinatura = assinatura_service.criar_assinatura(
        alvo, dados.id_plano, dados.data_inicio or date.today(), termino, status, valor)
    return assinatura_service.obter_assinatura(id_assinatura)


@router.put("/{id_assinatura}", response_model=AssinaturaOut)
def atualizar(id_assinatura: int, dados: AssinaturaIn,
              usuario: dict = Depends(usuario_atual)):
    atual = _ou_404(id_assinatura)
    _checar_dono(usuario, atual)

    if eh_admin(usuario):
        alvo = dados.id_usuario or atual["id_usuario"]
        status, termino, valor = dados.status or "ativa", dados.data_termino, dados.valor
        if not obter_usuario_publico(alvo):
            raise HTTPException(404, "Usuário não encontrado.")
    else:
        if (dados.id_usuario not in (None, usuario["id_usuario"])
                or dados.status not in (None, atual["status"])
                or dados.data_termino is not None or dados.valor is not None):
            raise HTTPException(403, _SO_ADMIN)
        alvo, status, termino, valor = (atual["id_usuario"], atual["status"],
                                        atual["data_termino"], None)

    # Mesmo plano e valor não informado: preserva o preço da época (regra do plano_service).
    if valor is None and dados.id_plano == atual["id_plano"]:
        valor = atual["valor"]

    assinatura_service.atualizar_assinatura(
        id_assinatura, alvo, dados.id_plano, dados.data_inicio or atual["data_inicio"],
        termino, status, valor)
    return assinatura_service.obter_assinatura(id_assinatura)


@router.patch("/{id_assinatura}/cancelar", response_model=AssinaturaOut)
def cancelar(id_assinatura: int, dados: Optional[CancelarIn] = None,
             usuario: dict = Depends(usuario_atual)):
    ass = _ou_404(id_assinatura)
    _checar_dono(usuario, ass)
    if ass["status"] != "ativa":
        raise HTTPException(409, "Somente assinaturas ativas podem ser canceladas.")
    termino = dados.data_termino if (dados and eh_admin(usuario)) else None
    assinatura_service.encerrar_assinatura(id_assinatura, termino, "cancelada")
    return assinatura_service.obter_assinatura(id_assinatura)


ROTEADORES = [router]
