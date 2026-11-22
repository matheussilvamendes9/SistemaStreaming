"""Instala a estrutura do banco operacional a partir de criar_tabelas.sql.

Execute na raiz do projeto ou diretamente pela pasta Base de Dados B.
Requer o connection.py do projeto e o schema streaming_db previamente criado.
"""

from pathlib import Path
import sys

import mysql.connector

# Permite que connection.py importe `database.erros` a partir da raiz do projeto.
PASTA_ATUAL = Path(__file__).resolve().parent
RAIZ_PROJETO = PASTA_ATUAL.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from connection import get_connection  # noqa: E402

ARQUIVO_SQL = PASTA_ATUAL / "criar_tabelas.sql"
BANCO_ESPERADO = "streaming_db"


def separar_instrucoes(texto):
    """Separa SQL por delimitadores, preservando corpos BEGIN ... END.

    Trata comentarios de linha e strings SQL; nao e um parser SQL generico.
    E suficiente para o arquivo criar_tabelas.sql deste projeto.
    """
    delimitador = ";"
    buffer = []
    instrucoes = []
    aspas = None
    comentario_bloco = False
    i = 0

    while i < len(texto):
        if not aspas and not comentario_bloco and (i == 0 or texto[i - 1] == "\n"):
            # A diretiva DELIMITER pertence ao cliente MySQL, nao ao servidor.
            fim = texto.find("\n", i)
            if fim == -1:
                fim = len(texto)
            linha = texto[i:fim].strip()
            if linha.upper().startswith("DELIMITER "):
                if "".join(buffer).strip():
                    raise ValueError("Diretiva DELIMITER encontrada no meio de uma instrucao SQL")
                delimitador = linha.split(None, 1)[1].strip()
                if not delimitador:
                    raise ValueError("Delimitador SQL vazio")
                i = fim + (fim < len(texto))
                continue

        if comentario_bloco:
            if texto.startswith("*/", i):
                comentario_bloco = False
                i += 2
            else:
                i += 1
            continue

        if aspas:
            caractere = texto[i]
            buffer.append(caractere)
            if caractere == "\\" and i + 1 < len(texto):
                i += 1
                buffer.append(texto[i])
            elif caractere == aspas:
                if i + 1 < len(texto) and texto[i + 1] == aspas:
                    i += 1
                    buffer.append(texto[i])
                else:
                    aspas = None
            i += 1
            continue

        if texto.startswith("--", i) and (i + 2 == len(texto) or texto[i + 2].isspace()):
            fim = texto.find("\n", i)
            i = len(texto) if fim == -1 else fim
            continue
        if texto[i] == "#":
            fim = texto.find("\n", i)
            i = len(texto) if fim == -1 else fim
            continue
        if texto.startswith("/*", i):
            comentario_bloco = True
            i += 2
            continue
        if texto[i] in ("'", '"', "`"):
            aspas = texto[i]
            buffer.append(texto[i])
            i += 1
            continue
        if texto.startswith(delimitador, i):
            instrucao = "".join(buffer).strip()
            if instrucao:
                instrucoes.append(instrucao)
            buffer.clear()
            i += len(delimitador)
            continue

        buffer.append(texto[i])
        i += 1

    if aspas or comentario_bloco:
        raise ValueError("String ou comentario SQL nao foi encerrado")
    if "".join(buffer).strip():
        raise ValueError("Instrucao SQL sem delimitador final")
    return instrucoes


def criar_banco():
    if not ARQUIVO_SQL.is_file():
        raise FileNotFoundError(f"Arquivo SQL nao encontrado: {ARQUIVO_SQL}")

    sql = ARQUIVO_SQL.read_text(encoding="utf-8-sig")
    instrucoes = separar_instrucoes(sql)
    if not instrucoes:
        raise ValueError("O arquivo SQL nao contem instrucoes")

    conexao = None
    cursor = None
    try:
        conexao = get_connection("streaming")
        cursor = conexao.cursor()
        cursor.execute("SELECT DATABASE()")
        banco_atual = cursor.fetchone()[0]
        if banco_atual != BANCO_ESPERADO:
            raise RuntimeError(
                f"Banco selecionado: {banco_atual!r}. Esperado: {BANCO_ESPERADO!r}. "
                "Verifique DB_STREAMING_NAME no .env."
            )

        print(f"Banco selecionado: {banco_atual}")
        print(f"Instrucoes encontradas: {len(instrucoes)}")
        for numero, instrucao in enumerate(instrucoes, start=1):
            descricao = " ".join(instrucao.split())[:90]
            print(f"[{numero}/{len(instrucoes)}] {descricao} ...")
            try:
                cursor.execute(instrucao)
            except mysql.connector.Error as erro:
                print(f"Erro na instrucao {numero}: {descricao}")
                raise

        conexao.commit()
        print("Estrutura do streaming_db aplicada com sucesso!")

    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    try:
        criar_banco()
    except (mysql.connector.Error, OSError, ValueError, RuntimeError) as erro:
        print(f"Falha ao aplicar a estrutura: {erro}", file=sys.stderr)
        print(
            "ATENCAO: instrucoes DDL ja executadas podem ter sido confirmadas pelo MySQL.",
            file=sys.stderr,
        )
        sys.exit(1)
