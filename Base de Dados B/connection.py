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


# Erros 1062 cuja causa e conhecida; a chave e procurada no texto do erro.
MENSAGENS_1062 = {
    "uq_assinatura_usuario_ativo": "O usuario ja possui uma assinatura ativa.",
    "uq_usuario_email": "Ja existe um usuario cadastrado com esse e-mail.",
    "uq_plano_nome": "Ja existe um plano com esse nome.",
    "uq_genero_nome": "Ja existe um genero com esse nome.",
    "uq_episodio_serie_temporada_numero": "Ja existe um episodio com essa temporada e numero nessa serie.",
}


def traduzir_erro(e):
    """Retorna a mensagem amigavel para um erro do MySQL, ou None."""
    if e.errno == 1644:
        # SIGNAL SQLSTATE '45000' dos triggers: a mensagem ja esta em portugues.
        return e.msg
    if e.errno == 1062:
        texto = e.msg or ""
        for chave, mensagem in MENSAGENS_1062.items():
            if chave in texto:
                return mensagem
    return MENSAGENS_ERRO.get(e.errno)


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
        mensagem = traduzir_erro(e)
        if mensagem:
            raise ErroAplicacao(mensagem) from e
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