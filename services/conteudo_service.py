"""RF02, RF03 (associacao) e RF06 (catalogo)."""
from database.connection import consultar, executar, transacao
from database.erros import ErroAplicacao
from services.validators import exigir_texto, validar_inteiro, validar_opcao

TIPOS = ("filme", "serie")


def _validar(titulo, tipo, ano, duracao):
    titulo = exigir_texto(titulo, "titulo", 150)
    tipo = validar_opcao(tipo, TIPOS, "tipo")
    ano = validar_inteiro(ano, "ano de lancamento", 1888, 2100)
    if tipo == "filme":
        duracao = validar_inteiro(duracao, "duracao (minutos)", 1)
    else:  # serie: duracao opcional
        duracao = validar_inteiro(duracao, "duracao (minutos)", 1) if duracao else None
    return titulo, tipo, ano, duracao


def _gravar_generos(cur, id_conteudo, ids_generos):
    cur.execute("DELETE FROM conteudo_genero WHERE id_conteudo = %s", (id_conteudo,))
    ids = sorted(set(ids_generos or []))
    if ids:
        cur.executemany(
            "INSERT INTO conteudo_genero (id_conteudo, id_genero) VALUES (%s, %s)",
            [(id_conteudo, int(g)) for g in ids],
        )


def criar_conteudo(titulo, tipo, ano_lancamento, duracao_minutos=None, ids_generos=None):
    dados = _validar(titulo, tipo, ano_lancamento, duracao_minutos)
    with transacao() as cur:
        cur.execute(
            "INSERT INTO conteudo (titulo, tipo, ano_lancamento, duracao_minutos) "
            "VALUES (%s, %s, %s, %s)", dados)
        id_conteudo = cur.lastrowid
        _gravar_generos(cur, id_conteudo, ids_generos)
    return id_conteudo


def atualizar_conteudo(id_conteudo, titulo, tipo, ano_lancamento,
                       duracao_minutos=None, ids_generos=None):
    dados = _validar(titulo, tipo, ano_lancamento, duracao_minutos)
    with transacao() as cur:
        cur.execute(
            "UPDATE conteudo SET titulo=%s, tipo=%s, ano_lancamento=%s, duracao_minutos=%s "
            "WHERE id_conteudo=%s", (*dados, id_conteudo))
        _gravar_generos(cur, id_conteudo, ids_generos)


def excluir_conteudo(id_conteudo):
    if not obter_conteudo(id_conteudo):
        raise ErroAplicacao("Conteudo nao encontrado.")
    executar("DELETE FROM conteudo WHERE id_conteudo = %s", (id_conteudo,))


def obter_conteudo(id_conteudo):
    r = consultar("SELECT * FROM conteudo WHERE id_conteudo = %s", (id_conteudo,))
    if not r:
        return None
    conteudo = r[0]
    conteudo["ids_generos"] = [
        x["id_genero"] for x in consultar(
            "SELECT id_genero FROM conteudo_genero WHERE id_conteudo = %s", (id_conteudo,))
    ]
    return conteudo


def listar_catalogo(busca=None, tipo=None, id_genero=None):
    """RF06: titulo, tipo, ano, duracao e generos de cada conteudo."""
    sql = """
        SELECT c.id_conteudo, c.titulo, c.tipo, c.ano_lancamento, c.duracao_minutos,
               COALESCE(GROUP_CONCAT(g.nome ORDER BY g.nome SEPARATOR ', '), '') AS generos
        FROM conteudo c
        LEFT JOIN conteudo_genero cg ON cg.id_conteudo = c.id_conteudo
        LEFT JOIN genero g ON g.id_genero = cg.id_genero
        WHERE 1 = 1
    """
    params = []
    if busca and busca.strip():
        sql += " AND c.titulo LIKE %s"
        params.append(f"%{busca.strip()}%")
    if tipo in TIPOS:
        sql += " AND c.tipo = %s"
        params.append(tipo)
    if id_genero:
        sql += " AND c.id_conteudo IN (SELECT id_conteudo FROM conteudo_genero WHERE id_genero = %s)"
        params.append(int(id_genero))
    sql += " GROUP BY c.id_conteudo, c.titulo, c.tipo, c.ano_lancamento, c.duracao_minutos ORDER BY c.titulo"
    return consultar(sql, tuple(params))