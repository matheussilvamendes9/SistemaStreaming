
from copy import deepcopy
from datetime import datetime, timedelta

from mocks.usuarios_mock import listar_usuarios
from mocks.catalogo_mock import (
    listar_catalogo,
    listar_episodios as listar_episodios_da_serie
)


# Registros fictícios iniciais para testes
HISTORICO = [
    {
        "id_reproducao": 1,
        "id_usuario": 2,
        "id_conteudo": 1,
        "id_episodio": None,
        "data_hora": datetime.now() - timedelta(days=3),
        "progresso_minutos": 120
    },
    {
        "id_reproducao": 2,
        "id_usuario": 2,
        "id_conteudo": 2,
        "id_episodio": 1,
        "data_hora": datetime.now() - timedelta(days=2),
        "progresso_minutos": 40
    },
    {
        "id_reproducao": 3,
        "id_usuario": 2,
        "id_conteudo": 2,
        "id_episodio": 2,
        "data_hora": datetime.now() - timedelta(days=1),
        "progresso_minutos": 35
    },
    {
        "id_reproducao": 4,
        "id_usuario": 1,
        "id_conteudo": 3,
        "id_episodio": None,
        "data_hora": datetime.now(),
        "progresso_minutos": 90
    }
]


def listar_episodios():
    """
    Retorna os episódios de todas as séries do catálogo.
    O catálogo original recebe o ID de uma série, então
    percorremos as séries para reunir todos os episódios.
    """
    catalogo = listar_catalogo()
    episodios = []

    for conteudo in catalogo:
        if conteudo["tipo"] == "serie":
            episodios.extend(
                listar_episodios_da_serie(conteudo["id_conteudo"])
            )

    return episodios


def listar_historico():
    """
    Retorna o histórico com os nomes dos usuários,
    conteúdos e episódios, no formato esperado pela interface.
    """
    usuarios = {
        usuario["id_usuario"]: usuario
        for usuario in listar_usuarios()
    }

    catalogo = {
        conteudo["id_conteudo"]: conteudo
        for conteudo in listar_catalogo()
    }

    episodios = {
        episodio["id_episodio"]: episodio
        for episodio in listar_episodios()
    }

    resultado = []

    for registro in HISTORICO:
        usuario = usuarios.get(registro["id_usuario"])
        conteudo = catalogo.get(registro["id_conteudo"])

        # Ignora registros cujos dados relacionados não existem mais.
        if usuario is None or conteudo is None:
            continue

        episodio = None

        if registro["id_episodio"] is not None:
            episodio = episodios.get(registro["id_episodio"])

            if episodio is None:
                continue

        resultado.append({
            "id_reproducao": registro["id_reproducao"],
            "usuario": usuario["nome"],
            "conteudo": conteudo["titulo"],
            "tipo": conteudo["tipo"],
            "titulo_episodio": (
                episodio["titulo"] if episodio else None
            ),
            "episodio": (
                episodio["episodio"] if episodio else None
            ),
            "temporada": (
                episodio["temporada"] if episodio else None
            ),
            "data_hora": registro["data_hora"],
            "progresso_minutos": registro["progresso_minutos"]
        })

    return resultado


def registrar_reproducao(
    id_usuario,
    id_conteudo,
    id_episodio,
    progresso_minutos
):
    """Registra uma nova reprodução no histórico."""

    usuarios = listar_usuarios()
    catalogo = listar_catalogo()

    usuario = next(
        (u for u in usuarios if u["id_usuario"] == id_usuario),
        None
    )

    conteudo = next(
        (c for c in catalogo if c["id_conteudo"] == id_conteudo),
        None
    )

    if usuario is None:
        raise ValueError("Usuário não encontrado.")

    if conteudo is None:
        raise ValueError("Conteúdo não encontrado.")

    try:
        progresso_minutos = float(progresso_minutos)
    except (TypeError, ValueError):
        raise ValueError("Informe um progresso válido.")

    if progresso_minutos <= 0:
        raise ValueError("O progresso deve ser maior que zero.")

    if conteudo["tipo"] == "filme":
        if id_episodio is not None:
            raise ValueError("Filmes não possuem episódios.")

        duracao = conteudo["duracao_minutos"]

    else:
        episodios = listar_episodios()
        episodio = next(
            (
                e for e in episodios
                if e["id_episodio"] == id_episodio
                and e["id_serie"] == id_conteudo
            ),
            None
        )

        if episodio is None:
            raise ValueError("Episódio não encontrado.")

        duracao = episodio["duracao_minutos"]

    if duracao is not None and progresso_minutos > duracao:
        raise ValueError(
            "O progresso não pode ultrapassar a duração do conteúdo."
        )

    novo_id = max(
        (r["id_reproducao"] for r in HISTORICO),
        default=0
    ) + 1

    nova_reproducao = {
        "id_reproducao": novo_id,
        "id_usuario": id_usuario,
        "id_conteudo": id_conteudo,
        "id_episodio": id_episodio,
        "data_hora": datetime.now(),
        "progresso_minutos": progresso_minutos
    }

    HISTORICO.append(nova_reproducao)

    return deepcopy(nova_reproducao)


def excluir_reproducao(id_reproducao):
    """Exclui uma reprodução pelo seu identificador."""

    registro = next(
        (
            r for r in HISTORICO
            if r["id_reproducao"] == id_reproducao
        ),
        None
    )

    if registro is None:
        raise ValueError("Registro de reprodução não encontrado.")

    HISTORICO.remove(registro)
