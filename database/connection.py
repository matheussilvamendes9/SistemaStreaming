"""Camada de acesso ao MySQL (RNF06 e RNF07)."""
import os
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv

from database.erros import ErroAplicacao

load_dotenv()

BANCOS = {
    "streaming": os.getenv("DB_STREAMING_NAME", "streaming_db"),
    "analise": os.getenv("DB_ANALISE_NAME", "analise_db"),
}

MENSAGENS_ERRO = {
    1062: "Ja existe um registro com esse valor unico (ex.: e-mail ou nome repetido).",
    1451: "Nao e possivel excluir: o registro esta sendo usado por outros dados.",
    1452: "Referencia invalida: usuario, conteudo ou genero informado nao existe.",
    3819: "Algum valor viola as regras do banco (ex.: numero negativo ou datas inconsistentes).",
    4025: "Algum valor viola as regras do banco (ex.: numero negativo ou datas inconsistentes).",
}


def get_connection(banco="streaming"):
    if banco not in BANCOS:
        raise ValueError(f"Banco desconhecido: {banco}")
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=BANCOS[banco],
        charset="utf8mb4",
    )


def consultar(sql, params=None, banco="streaming"):
    """SELECT -> lista de dicionarios."""
    conn = get_connection(banco)
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params or ())
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@contextmanager
def transacao(banco="streaming"):
    """Commit se tudo der certo, rollback se der erro."""
    conn = get_connection(banco)
    cur = conn.cursor(dictionary=True)
    try:
        yield cur
        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        if e.errno in MENSAGENS_ERRO:
            raise ErroAplicacao(MENSAGENS_ERRO[e.errno]) from e
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def executar(sql, params=None, banco="streaming"):
    """INSERT/UPDATE/DELETE. Retorna o ultimo id inserido."""
    with transacao(banco) as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid