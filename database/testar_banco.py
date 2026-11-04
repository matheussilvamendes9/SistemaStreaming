"""Testes de integridade do Banco B (streaming_db).

Execute depois de aplicar criar_tabelas.sql:
    python "Base de Dados B/testar_banco.py"

Requer connection.py, mysql-connector-python e as configuracoes do .env.
Os testes de escrita sao revertidos por ROLLBACK (nao usam DDL).
"""

from pathlib import Path
import sys
import uuid

import mysql.connector

PASTA_ATUAL = Path(__file__).resolve().parent
RAIZ_PROJETO = PASTA_ATUAL.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from connection import get_connection  # noqa: E402

BANCO_ESPERADO = "streaming_db"
TABELAS = {
    "usuario", "plano", "assinatura", "conteudo", "episodio",
    "genero", "conteudo_genero", "historico_reproducao",
}
TRIGGERS = {
    "trg_episodio_bi", "trg_episodio_bu", "trg_historico_bi",
    "trg_historico_bu", "trg_conteudo_bu", "trg_assinatura_bi",
    "trg_assinatura_bu",
}
PLANOS = {"basico": "20.00", "padrao": "35.00", "premium": "50.00"}

# Codigos de erro esperados em cada tipo de violacao.
ERRO_CHECK = (3819, 4025)   # CHECK (4025 e o equivalente no MariaDB)
ERRO_DUPLICADO = (1062,)    # UNIQUE / PRIMARY KEY
ERRO_FK_FILHO = (1452,)     # linha filha sem pai correspondente
ERRO_FK_PAI = (1451,)       # excluir pai ainda referenciado (RESTRICT)
ERRO_TRIGGER = (1644,)      # SIGNAL SQLSTATE '45000'


class FalhaTeste(AssertionError):
    pass


def verificar(condicao, mensagem):
    if not condicao:
        raise FalhaTeste(mensagem)


def inserir(cur, sql, parametros):
    cur.execute(sql, parametros)
    return cur.lastrowid


def deve_falhar(cur, sql, parametros, descricao, erros_esperados):
    """Executa uma operacao invalida.

    Falha se o banco a permitir ou se ela for recusada por um motivo
    diferente do esperado (evita aprovar o teste pelo erro errado).
    """
    try:
        cur.execute(sql, parametros)
    except mysql.connector.Error as erro:
        if erro.errno not in erros_esperados:
            raise FalhaTeste(
                f"{descricao}: erro {erro.errno} em vez de {erros_esperados}: {erro}"
            ) from erro
        return
    raise FalhaTeste(f"O banco permitiu: {descricao}")


def executar_teste(nome, funcao, conexao, resultados):
    """Isola cada teste em uma transacao descartada integralmente."""
    try:
        conexao.rollback()
        conexao.start_transaction()
        cur = conexao.cursor()
        try:
            funcao(cur)
            resultados.append((nome, True, ""))
            print(f"[OK]    {nome}")
        finally:
            cur.close()
    except Exception as erro:
        resultados.append((nome, False, f"{type(erro).__name__}: {erro}"))
        print(f"[FALHA] {nome}: {type(erro).__name__}: {erro}")
    finally:
        # Nada criado durante o teste permanece no banco.
        conexao.rollback()


def dados_usuario(cur):
    token = uuid.uuid4().hex[:16]
    return inserir(
        cur,
        "INSERT INTO usuario (nome, email) VALUES (%s, %s)",
        ("Usuario de teste", f"teste_{token}@example.invalid"),
    )


def dados_conteudo(cur, tipo):
    return inserir(
        cur,
        "INSERT INTO conteudo (titulo, tipo, ano_lancamento, duracao_minutos) "
        "VALUES (%s, %s, %s, %s)",
        (f"Conteudo teste {uuid.uuid4().hex[:12]}", tipo, 2024,
         120 if tipo == "filme" else None),
    )


def dados_episodio(cur, serie):
    return inserir(
        cur,
        "INSERT INTO episodio (id_serie, titulo, temporada, episodio, duracao_minutos) "
        "VALUES (%s, %s, %s, %s, %s)",
        (serie, "Piloto", 1, 1, 42),
    )


def id_plano(cur, nome="basico"):
    cur.execute("SELECT id_plano FROM plano WHERE nome = %s", (nome,))
    linha = cur.fetchone()
    verificar(linha is not None, f"Plano {nome!r} nao encontrado")
    return linha[0]


def teste_tabelas(cur):
    cur.execute("SHOW TABLES")
    existentes = {linha[0] for linha in cur.fetchall()}
    verificar(TABELAS <= existentes, f"Tabelas ausentes: {sorted(TABELAS - existentes)}")


def teste_triggers(cur):
    cur.execute("SHOW TRIGGERS")
    existentes = {linha[0] for linha in cur.fetchall()}
    verificar(TRIGGERS <= existentes, f"Triggers ausentes: {sorted(TRIGGERS - existentes)}")


def teste_planos(cur):
    cur.execute("SELECT nome, valor FROM plano WHERE nome IN ('basico','padrao','premium')")
    encontrados = {nome: str(valor) for nome, valor in cur.fetchall()}
    verificar(encontrados == PLANOS,
              f"Planos esperados {PLANOS}; encontrados {encontrados}")


def teste_email_unico(cur):
    usuario = dados_usuario(cur)
    cur.execute("SELECT email FROM usuario WHERE id_usuario = %s", (usuario,))
    email = cur.fetchone()[0]
    deve_falhar(cur, "INSERT INTO usuario (nome, email) VALUES (%s, %s)",
                ("Outro usuario", email), "e-mail duplicado", ERRO_DUPLICADO)


def teste_checks(cur):
    deve_falhar(cur, "INSERT INTO plano (nome, valor) VALUES (%s, %s)",
                (f"invalido_{uuid.uuid4().hex[:8]}", 0), "plano com valor zero", ERRO_CHECK)
    deve_falhar(cur, "INSERT INTO conteudo (titulo, tipo, ano_lancamento, duracao_minutos) "
                "VALUES (%s, %s, %s, %s)",
                ("Filme invalido", "filme", 2024, None), "filme sem duracao", ERRO_CHECK)
    deve_falhar(cur, "INSERT INTO conteudo (titulo, tipo, ano_lancamento, duracao_minutos) "
                "VALUES (%s, %s, %s, %s)",
                ("Serie invalida", "serie", 2024, 60), "serie com duracao total", ERRO_CHECK)


def teste_assinatura_unica(cur):
    usuario = dados_usuario(cur)
    plano = id_plano(cur)
    primeira = inserir(cur,
        "INSERT INTO assinatura (id_usuario, id_plano, valor, data_inicio, status) "
        "VALUES (%s, %s, %s, %s, %s)",
        (usuario, plano, 20, "2026-01-01", "ativa"))
    cur.execute("SELECT usuario_ativo FROM assinatura WHERE id_assinatura = %s", (primeira,))
    verificar(cur.fetchone()[0] == usuario, "Trigger nao definiu usuario_ativo")
    deve_falhar(cur,
        "INSERT INTO assinatura (id_usuario, id_plano, valor, data_inicio, status) "
        "VALUES (%s, %s, %s, %s, %s)",
        (usuario, plano, 20, "2026-02-01", "ativa"),
        "duas assinaturas ativas do mesmo usuario", ERRO_DUPLICADO)
    cur.execute("UPDATE assinatura SET status = 'cancelada', data_termino = %s "
                "WHERE id_assinatura = %s", ("2026-01-31", primeira))
    cur.execute("SELECT usuario_ativo FROM assinatura WHERE id_assinatura = %s", (primeira,))
    verificar(cur.fetchone()[0] is None, "Trigger nao limpou usuario_ativo")
    inserir(cur,
        "INSERT INTO assinatura (id_usuario, id_plano, valor, data_inicio, status) "
        "VALUES (%s, %s, %s, %s, %s)",
        (usuario, plano, 20, "2026-02-01", "ativa"))


def teste_episodio_somente_serie(cur):
    filme = dados_conteudo(cur, "filme")
    deve_falhar(cur,
        "INSERT INTO episodio (id_serie, titulo, temporada, episodio, duracao_minutos) "
        "VALUES (%s, %s, %s, %s, %s)",
        (filme, "Invalido", 1, 1, 30), "episodio associado a filme", ERRO_TRIGGER)
    serie = dados_conteudo(cur, "serie")
    dados_episodio(cur, serie)
    deve_falhar(cur,
        "INSERT INTO episodio (id_serie, titulo, temporada, episodio, duracao_minutos) "
        "VALUES (%s, %s, %s, %s, %s)",
        (serie, "Duplicado", 1, 1, 30), "numero de episodio duplicado", ERRO_DUPLICADO)


def teste_historico(cur):
    usuario = dados_usuario(cur)
    filme = dados_conteudo(cur, "filme")
    serie = dados_conteudo(cur, "serie")
    episodio = dados_episodio(cur, serie)
    inserir(cur,
        "INSERT INTO historico_reproducao (id_usuario, id_conteudo, id_episodio, progresso_minutos) "
        "VALUES (%s, %s, %s, %s)", (usuario, filme, None, 12))
    inserir(cur,
        "INSERT INTO historico_reproducao (id_usuario, id_conteudo, id_episodio, progresso_minutos) "
        "VALUES (%s, %s, %s, %s)", (usuario, serie, episodio, 10))
    comando = ("INSERT INTO historico_reproducao "
               "(id_usuario, id_conteudo, id_episodio, progresso_minutos) "
               "VALUES (%s, %s, %s, %s)")
    deve_falhar(cur, comando, (usuario, serie, None, 0), "serie sem episodio", ERRO_TRIGGER)
    deve_falhar(cur, comando, (usuario, filme, episodio, 0), "filme com episodio", ERRO_TRIGGER)
    outra_serie = dados_conteudo(cur, "serie")
    deve_falhar(cur, comando, (usuario, outra_serie, episodio, 0),
                "episodio de outra serie", ERRO_FK_FILHO)
    deve_falhar(cur, comando, (usuario, filme, None, -1), "progresso negativo", ERRO_CHECK)


def teste_fk(cur):
    deve_falhar(cur,
        "INSERT INTO assinatura (id_usuario, id_plano, valor, data_inicio) "
        "VALUES (%s, %s, %s, %s)",
        (4294967295, id_plano(cur), 20, "2026-01-01"),
        "assinatura com usuario inexistente", ERRO_FK_FILHO)


def teste_cascata_usuario(cur):
    usuario = dados_usuario(cur)
    plano = id_plano(cur)
    inserir(cur,
        "INSERT INTO assinatura (id_usuario, id_plano, valor, data_inicio) "
        "VALUES (%s, %s, %s, %s)", (usuario, plano, 20, "2026-01-01"))
    filme = dados_conteudo(cur, "filme")
    inserir(cur,
        "INSERT INTO historico_reproducao (id_usuario, id_conteudo) VALUES (%s, %s)",
        (usuario, filme))
    cur.execute("DELETE FROM usuario WHERE id_usuario = %s", (usuario,))
    cur.execute("SELECT COUNT(*) FROM assinatura WHERE id_usuario = %s", (usuario,))
    verificar(cur.fetchone()[0] == 0, "Assinatura nao foi excluida em cascata")
    cur.execute("SELECT COUNT(*) FROM historico_reproducao WHERE id_usuario = %s", (usuario,))
    verificar(cur.fetchone()[0] == 0, "Historico nao foi excluido em cascata")


def teste_cascata_conteudo(cur):
    usuario = dados_usuario(cur)
    serie = dados_conteudo(cur, "serie")
    episodio = dados_episodio(cur, serie)
    inserir(cur,
        "INSERT INTO historico_reproducao (id_usuario, id_conteudo, id_episodio) "
        "VALUES (%s, %s, %s)", (usuario, serie, episodio))
    genero = inserir(cur, "INSERT INTO genero (nome) VALUES (%s)",
                     (f"genero_teste_{uuid.uuid4().hex[:12]}",))
    inserir(cur, "INSERT INTO conteudo_genero (id_conteudo, id_genero) VALUES (%s, %s)",
            (serie, genero))
    cur.execute("DELETE FROM conteudo WHERE id_conteudo = %s", (serie,))
    cur.execute("SELECT COUNT(*) FROM episodio WHERE id_serie = %s", (serie,))
    verificar(cur.fetchone()[0] == 0, "Episodio nao foi excluido em cascata")
    cur.execute("SELECT COUNT(*) FROM historico_reproducao WHERE id_conteudo = %s", (serie,))
    verificar(cur.fetchone()[0] == 0, "Historico nao foi excluido em cascata")
    cur.execute("SELECT COUNT(*) FROM conteudo_genero WHERE id_conteudo = %s", (serie,))
    verificar(cur.fetchone()[0] == 0, "Vinculo de genero nao foi excluido em cascata")
    cur.execute("SELECT COUNT(*) FROM genero WHERE id_genero = %s", (genero,))
    verificar(cur.fetchone()[0] == 1, "Genero nao deveria ser excluido junto com o conteudo")


def teste_alteracao_tipo(cur):
    serie = dados_conteudo(cur, "serie")
    dados_episodio(cur, serie)
    deve_falhar(cur,
        "UPDATE conteudo SET tipo = %s, duracao_minutos = %s WHERE id_conteudo = %s",
        ("filme", 100, serie), "transformar serie com episodios em filme", ERRO_TRIGGER)


def teste_status_assinatura(cur):
    usuario = dados_usuario(cur)
    plano = id_plano(cur)
    comando = ("INSERT INTO assinatura "
               "(id_usuario, id_plano, valor, data_inicio, data_termino, status) "
               "VALUES (%s, %s, %s, %s, %s, %s)")
    deve_falhar(cur, comando, (usuario, plano, 20, "2026-01-01", "2026-02-01", "ativa"),
                "assinatura ativa com data de termino", ERRO_CHECK)
    deve_falhar(cur, comando, (usuario, plano, 20, "2026-01-01", None, "cancelada"),
                "assinatura cancelada sem data de termino", ERRO_CHECK)
    deve_falhar(cur, comando, (usuario, plano, 20, "2026-02-01", "2026-01-01", "cancelada"),
                "data de termino anterior ao inicio", ERRO_CHECK)


def teste_plano_restrito(cur):
    usuario = dados_usuario(cur)
    plano = inserir(cur, "INSERT INTO plano (nome, valor) VALUES (%s, %s)",
                    (f"teste_{uuid.uuid4().hex[:12]}", 10))
    inserir(cur,
        "INSERT INTO assinatura (id_usuario, id_plano, valor, data_inicio) "
        "VALUES (%s, %s, %s, %s)", (usuario, plano, 10, "2026-01-01"))
    deve_falhar(cur, "DELETE FROM plano WHERE id_plano = %s", (plano,),
                "excluir plano que possui assinaturas", ERRO_FK_PAI)
    cur.execute("DELETE FROM assinatura WHERE id_usuario = %s", (usuario,))
    cur.execute("DELETE FROM plano WHERE id_plano = %s", (plano,))
    cur.execute("SELECT COUNT(*) FROM plano WHERE id_plano = %s", (plano,))
    verificar(cur.fetchone()[0] == 0, "Plano sem assinaturas deveria poder ser excluido")


def main():
    testes = [
        ("Oito tabelas presentes", teste_tabelas),
        ("Sete triggers presentes", teste_triggers),
        ("Planos iniciais e valores", teste_planos),
        ("E-mail unico", teste_email_unico),
        ("Restricoes CHECK", teste_checks),
        ("Uma assinatura ativa por usuario", teste_assinatura_unica),
        ("Status e datas da assinatura", teste_status_assinatura),
        ("Episodios somente em series e sem duplicidade", teste_episodio_somente_serie),
        ("Historico de filmes e series", teste_historico),
        ("Chaves estrangeiras", teste_fk),
        ("Exclusao em cascata de usuario", teste_cascata_usuario),
        ("Exclusao em cascata de conteudo (genero preservado)", teste_cascata_conteudo),
        ("Plano com assinaturas nao pode ser excluido", teste_plano_restrito),
        ("Protecao contra mudanca de tipo", teste_alteracao_tipo),
    ]
    conexao = None
    try:
        conexao = get_connection("streaming")
        cur = conexao.cursor()
        try:
            cur.execute("SELECT DATABASE()")
            banco = cur.fetchone()[0]
            if banco != BANCO_ESPERADO:
                raise RuntimeError(f"Banco selecionado: {banco!r}; esperado: {BANCO_ESPERADO!r}")
        finally:
            cur.close()
        print(f"Banco: {BANCO_ESPERADO} | Testes com ROLLBACK\n")
        resultados = []
        for nome, funcao in testes:
            executar_teste(nome, funcao, conexao, resultados)
        aprovados = sum(ok for _, ok, _ in resultados)
        print(f"\nRESULTADO: {aprovados}/{len(testes)} testes aprovados.")
        print("Dados temporarios dos testes foram revertidos (ROLLBACK).")
        return 0 if aprovados == len(testes) else 1
    except (mysql.connector.Error, OSError, ValueError, RuntimeError) as erro:
        print(f"Nao foi possivel executar os testes: {erro}", file=sys.stderr)
        return 2
    finally:
        if conexao is not None:
            conexao.rollback()
            conexao.close()


if __name__ == "__main__":
    sys.exit(main())