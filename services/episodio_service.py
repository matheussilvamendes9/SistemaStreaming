"""CRUD de episodios (tabela 'episodio'; so existem para conteudos do tipo serie)."""
from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import exigir_texto, validar_inteiro


def _validar(titulo, temporada, numero, duracao):
    titulo = exigir_texto(titulo, "titulo do episodio", 255)
    temporada = validar_inteiro(temporada, "temporada", 1, 65535)
    numero = validar_inteiro(numero, "numero do episodio", 1, 65535)
    duracao = validar_inteiro(duracao, "duracao (minutos)", 1)
    return titulo, temporada, numero, duracao


def listar_episodios(id_serie=None):
    sql = """
        SELECT e.id_episodio, e.id_serie, c.titulo AS serie, e.titulo,
               e.temporada, e.episodio, e.duracao_minutos
        FROM episodio e
        JOIN conteudo c ON c.id_conteudo = e.id_serie
    """
    params = []
    if id_serie:
        sql += " WHERE e.id_serie = %s"
        params.append(int(id_serie))
    sql += " ORDER BY c.titulo, e.temporada, e.episodio"
    return consultar(sql, tuple(params))


def obter_episodio(id_episodio):
    r = consultar("SELECT * FROM episodio WHERE id_episodio = %s", (id_episodio,))
    return r[0] if r else None


def criar_episodio(id_serie, titulo, temporada, numero, duracao_minutos):
    """O banco recusa se id_serie nao for um conteudo do tipo 'serie'."""
    id_serie = validar_inteiro(id_serie, "serie", 1)
    dados = _validar(titulo, temporada, numero, duracao_minutos)
    return executar(
        "INSERT INTO episodio (id_serie, titulo, temporada, episodio, duracao_minutos) "
        "VALUES (%s, %s, %s, %s, %s)", (id_serie, *dados))


def atualizar_episodio(id_episodio, titulo, temporada, numero, duracao_minutos):
    dados = _validar(titulo, temporada, numero, duracao_minutos)
    executar(
        "UPDATE episodio SET titulo=%s, temporada=%s, episodio=%s, duracao_minutos=%s "
        "WHERE id_episodio=%s", (*dados, id_episodio))


def excluir_episodio(id_episodio):
    """Apaga tambem as reproducoes desse episodio (CASCADE)."""
    if not obter_episodio(id_episodio):
        raise ErroAplicacao("Episodio nao encontrado.")
    executar("DELETE FROM episodio WHERE id_episodio = %s", (id_episodio,))