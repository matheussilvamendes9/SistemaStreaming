from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from api.dependencies import exigir_admin
from api.schemas import UsuarioAtualizarIn, UsuarioCriarIn, UsuarioOut
from services import usuario_service
from services.auth_service import (ConflitoErro, criar_conta, definir_papel,
                                   definir_senha, listar_usuarios_publico,
                                   obter_por_email, obter_usuario_publico)

router = APIRouter(prefix="/usuarios", tags=["Usuários (admin)"])


def _ou_404(id_usuario):
    usuario = obter_usuario_publico(id_usuario)
    if not usuario:
        raise HTTPException(404, "Usuário não encontrado.")
    return usuario


@router.get("", response_model=list[UsuarioOut])
def listar(busca: Optional[str] = None, _: dict = Depends(exigir_admin)):
    return listar_usuarios_publico(busca)


@router.get("/{id_usuario}", response_model=UsuarioOut)
def consultar(id_usuario: int, _: dict = Depends(exigir_admin)):
    return _ou_404(id_usuario)


@router.post("", response_model=UsuarioOut, status_code=201)
def criar(dados: UsuarioCriarIn, _: dict = Depends(exigir_admin)):
    id_usuario = criar_conta(dados.nome, dados.email, dados.senha, dados.papel)
    return obter_usuario_publico(id_usuario)


@router.put("/{id_usuario}", response_model=UsuarioOut)
def atualizar(id_usuario: int, dados: UsuarioAtualizarIn,
              admin: dict = Depends(exigir_admin)):
    atual = _ou_404(id_usuario)
    if (dados.papel and dados.papel != "admin"
            and id_usuario == admin["id_usuario"]):
        raise HTTPException(400, "Você não pode remover o seu próprio papel de administrador.")
    outro = obter_por_email(dados.email.strip().lower())
    if outro and outro["id_usuario"] != id_usuario:
        raise ConflitoErro("E-mail já cadastrado.")

    usuario_service.atualizar_usuario(id_usuario, dados.nome, dados.email)  # lógica existente
    if dados.senha:
        definir_senha(id_usuario, dados.senha)
    if dados.papel and dados.papel != atual["papel"]:
        definir_papel(id_usuario, dados.papel)
    return obter_usuario_publico(id_usuario)


@router.delete("/{id_usuario}", status_code=204, response_class=Response)
def excluir(id_usuario: int, admin: dict = Depends(exigir_admin)):
    if id_usuario == admin["id_usuario"]:
        raise HTTPException(400, "Você não pode excluir a sua própria conta.")
    usuario_service.excluir_usuario(id_usuario)  # lança "não encontrado" -> 404
    return Response(status_code=204)


ROTEADORES = [router]
