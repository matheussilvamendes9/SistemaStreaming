"""Modelos Pydantic (formatos JSON do contrato)."""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Papel = Literal["admin", "usuario"]
StatusAssinatura = Literal["ativa", "cancelada", "expirada"]


class _Estrito(BaseModel):
    """Rejeita campos desconhecidos (ex.: 'papel' no cadastro comum)."""
    model_config = ConfigDict(extra="forbid")


# ---------- Autenticação / usuários ----------
class LoginIn(_Estrito):
    email: str
    senha: str


class UsuarioOut(BaseModel):
    id_usuario: int
    nome: str
    email: str
    papel: str
    data_cadastro: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


def validar_limite_bcrypt(senha: str) -> str:
    if len(senha.encode("utf-8")) > 72:
        raise ValueError(
            "A senha deve ter no máximo 72 bytes."
        )
    return senha


class RegistroIn(_Estrito):
    nome: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=255)
    senha: str = Field(min_length=8)
    id_plano: int = Field(gt=0)

    @field_validator("senha")
    @classmethod
    def validar_bytes_senha(cls, senha):
        return validar_limite_bcrypt(senha)


class UsuarioCriarIn(RegistroIn):
    papel: Papel = "usuario"


class UsuarioAtualizarIn(_Estrito):
    nome: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=255)
    senha: Optional[str] = Field(default=None, min_length=8, max_length=72)
    papel: Optional[Papel] = None


# ---------- Catálogo ----------
class ConteudoIn(_Estrito):
    titulo: str
    tipo: str
    ano_lancamento: int
    duracao_minutos: Optional[int] = None
    ids_generos: list[int] = []


class ConteudoListaOut(BaseModel):
    id_conteudo: int
    titulo: str
    tipo: str
    ano_lancamento: int
    duracao_minutos: Optional[int] = None
    generos: str = ""
    total_episodios: int = 0


class ConteudoOut(BaseModel):
    id_conteudo: int
    titulo: str
    tipo: str
    ano_lancamento: int
    duracao_minutos: Optional[int] = None
    ids_generos: list[int] = []


class GeneroOut(BaseModel):
    id_genero: int
    nome: str
    total_conteudos: int


class EpisodioIn(_Estrito):
    titulo: str
    temporada: int
    episodio: int
    duracao_minutos: int


class EpisodioOut(BaseModel):
    id_episodio: int
    id_serie: int
    serie: Optional[str] = None
    titulo: str
    temporada: int
    episodio: int
    duracao_minutos: int


# ---------- Planos / assinaturas ----------
class PlanoOut(BaseModel):
    id_plano: int
    nome: str
    valor: float
    total_assinaturas: Optional[int] = None


class AssinaturaIn(_Estrito):
    id_usuario: Optional[int] = None      # usuário comum: ignorado/proibido outro id
    id_plano: int
    data_inicio: Optional[date] = None    # padrão: hoje
    data_termino: Optional[date] = None   # somente admin
    status: Optional[StatusAssinatura] = None  # somente admin
    valor: Optional[float] = None         # somente admin


class CancelarIn(_Estrito):
    data_termino: Optional[date] = None   # somente admin; padrão: hoje


class AssinaturaOut(BaseModel):
    id_assinatura: int
    id_usuario: int
    usuario: Optional[str] = None
    id_plano: int
    plano: Optional[str] = None
    valor: float
    data_inicio: date
    data_termino: Optional[date] = None
    status: str


# ---------- Histórico ----------
class HistoricoIn(_Estrito):
    id_usuario: Optional[int] = None      # usuário comum: sempre o próprio
    id_conteudo: int
    progresso_minutos: float = Field(ge=0)
    id_episodio: Optional[int] = None
    data_hora: Optional[datetime] = None


class HistoricoOut(BaseModel):
    id_reproducao: int
    usuario: str
    conteudo: str
    tipo: str
    temporada: Optional[int] = None
    episodio: Optional[int] = None
    titulo_episodio: Optional[str] = None
    data_hora: datetime
    progresso_minutos: float


class ReproducaoCriadaOut(BaseModel):
    id_reproducao: int


# ---------- Indicadores ----------
class TopConteudoOut(BaseModel):
    id_conteudo: int
    titulo: str
    tipo: str
    total_reproducoes: int


class IndicadoresOut(BaseModel):
    total_usuarios: int
    total_filmes: int
    total_series: int
    total_reproducoes: int
    assinaturas_ativas: int
    top_conteudos: list[TopConteudoOut]
