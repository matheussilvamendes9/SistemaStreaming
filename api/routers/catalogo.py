from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from api.dependencies import exigir_admin, usuario_atual
from api.schemas import (ConteudoIn, ConteudoListaOut, ConteudoOut, EpisodioIn,
                         EpisodioOut, GeneroOut)
from services import conteudo_service, episodio_service, genero_service

router_conteudos = APIRouter(prefix="/conteudos", tags=["Catálogo"])
router_generos = APIRouter(prefix="/generos", tags=["Catálogo"])


def _conteudo_ou_404(id_conteudo):
    conteudo = conteudo_service.obter_conteudo(id_conteudo)
    if not conteudo:
        raise HTTPException(404, "Conteúdo não encontrado.")
    return conteudo


# ---------- conteúdos ----------
@router_conteudos.get("", response_model=list[ConteudoListaOut])
def listar(busca: Optional[str] = None, tipo: Optional[str] = None,
           id_genero: Optional[int] = None, _: dict = Depends(usuario_atual)):
    return conteudo_service.listar_catalogo(busca, tipo, id_genero)


@router_conteudos.get("/{id_conteudo}", response_model=ConteudoOut)
def consultar(id_conteudo: int, _: dict = Depends(usuario_atual)):
    return _conteudo_ou_404(id_conteudo)


@router_conteudos.post("", response_model=ConteudoOut, status_code=201)
def criar(dados: ConteudoIn, _: dict = Depends(exigir_admin)):
    id_conteudo = conteudo_service.criar_conteudo(
        dados.titulo, dados.tipo, dados.ano_lancamento,
        dados.duracao_minutos, dados.ids_generos)
    return conteudo_service.obter_conteudo(id_conteudo)


@router_conteudos.put("/{id_conteudo}", response_model=ConteudoOut)
def atualizar(id_conteudo: int, dados: ConteudoIn, _: dict = Depends(exigir_admin)):
    _conteudo_ou_404(id_conteudo)
    conteudo_service.atualizar_conteudo(
        id_conteudo, dados.titulo, dados.tipo, dados.ano_lancamento,
        dados.duracao_minutos, dados.ids_generos)
    return conteudo_service.obter_conteudo(id_conteudo)


@router_conteudos.delete("/{id_conteudo}", status_code=204, response_class=Response)
def excluir(id_conteudo: int, _: dict = Depends(exigir_admin)):
    conteudo_service.excluir_conteudo(id_conteudo)  # "não encontrado" -> 404
    return Response(status_code=204)


# ---------- episódios ----------
@router_conteudos.get("/{id_conteudo}/episodios", response_model=list[EpisodioOut])
def listar_episodios(id_conteudo: int, _: dict = Depends(usuario_atual)):
    _conteudo_ou_404(id_conteudo)
    return episodio_service.listar_episodios(id_conteudo)


@router_conteudos.post("/{id_conteudo}/episodios", response_model=EpisodioOut,
                       status_code=201)
def criar_episodio(id_conteudo: int, dados: EpisodioIn,
                   _: dict = Depends(exigir_admin)):
    conteudo = _conteudo_ou_404(id_conteudo)
    if conteudo["tipo"] != "serie":
        raise HTTPException(400, "Filmes não possuem episódios.")
    id_episodio = episodio_service.criar_episodio(
        id_conteudo, dados.titulo, dados.temporada, dados.episodio,
        dados.duracao_minutos)
    return episodio_service.obter_episodio(id_episodio)


# ---------- gêneros ----------
@router_generos.get("", response_model=list[GeneroOut])
def listar_generos(_: dict = Depends(usuario_atual)):
    return genero_service.listar_generos()


ROTEADORES = [router_conteudos, router_generos]
