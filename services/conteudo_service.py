"""RF02, RF03 (associacao) e RF06 (catalogo)."""
from database.connection import consultar, executar, transacao
from database.erros import ErroAplicacao
from services.validators import exigir_texto, validar_inteiro, validar_opcao

TIPOS = ("filme", "serie")


def _validar(titulo, tipo, ano, duracao):
    titulo = exigir_texto(titulo, "titulo", 255)
    tipo = validar_opcao(tipo, TIPOS, "tipo")
    ano = validar_inteiro(ano, "ano de lancamento", 1888, 2100)
    if tipo == "filme":
        if duracao in (None, ""):
            raise ErroAplicacao("Filmes exigem a duracao em minutos.")
        duracao = validar_inteiro(duracao, "duracao (minutos)", 1)
    else:
        # Serie nao tem duracao propria: o banco exige NULL (a duracao fica nos episodios).
        duracao = None
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
    with transacao() as cur:  # conteudo + generos na mesma transacao
        cur.execute(
            "INSERT INTO conteudo (titulo, tipo, ano_lancamento, duracao_minutos) "
            "VALUES (%s, %s, %s, %s)", dados)
        id_conteudo = cur.lastrowid
        _gravar_generos(cur, id_conteudo, ids_generos)
    return id_conteudo


def atualizar_conteudo(id_conteudo, titulo, tipo, ano_lancamento,
                       duracao_minutos=None, ids_generos=None):
    """O banco bloqueia trocar o tipo de um conteudo que ja tem episodios ou historico."""
    dados = _validar(titulo, tipo, ano_lancamento, duracao_minutos)
    with transacao() as cur:
        cur.execute(
            "UPDATE conteudo SET titulo=%s, tipo=%s, ano_lancamento=%s, duracao_minutos=%s "
            "WHERE id_conteudo=%s", (*dados, id_conteudo))
        _gravar_generos(cur, id_conteudo, ids_generos)


def excluir_conteudo(id_conteudo):
    """Apaga tambem episodios, historico e vinculos de genero (CASCADE)."""
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
    """RF06: titulo, tipo, ano, duracao, generos e (para series) total de episodios."""
    sql = """
        SELECT c.id_conteudo, c.titulo, c.tipo, c.ano_lancamento, c.duracao_minutos,
               COALESCE(GROUP_CONCAT(g.nome ORDER BY g.nome SEPARATOR ', '), '') AS generos,
               (SELECT COUNT(*) FROM episodio e WHERE e.id_serie = c.id_conteudo) AS total_episodios
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
    sql += (" GROUP BY c.id_conteudo, c.titulo, c.tipo, c.ano_lancamento, c.duracao_minutos"
            " ORDER BY c.titulo")
    return consultar(sql, tuple(params))