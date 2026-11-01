"""RF03 - CRUD de generos."""
from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import exigir_texto


def listar_generos():
    return consultar("""
        SELECT g.id_genero, g.nome, COUNT(cg.id_conteudo) AS total_conteudos
        FROM genero g
        LEFT JOIN conteudo_genero cg ON cg.id_genero = g.id_genero
        GROUP BY g.id_genero, g.nome
        ORDER BY g.nome
    """)


def criar_genero(nome):
    nome = exigir_texto(nome, "nome do genero", 50)
    return executar("INSERT INTO genero (nome) VALUES (%s)", (nome,))


def atualizar_genero(id_genero, nome):
    nome = exigir_texto(nome, "nome do genero", 50)
    executar("UPDATE genero SET nome = %s WHERE id_genero = %s", (nome, id_genero))


def excluir_genero(id_genero):
    r = consultar("SELECT 1 FROM genero WHERE id_genero = %s", (id_genero,))
    if not r:
        raise ErroAplicacao("Genero nao encontrado.")
    executar("DELETE FROM genero WHERE id_genero = %s", (id_genero,))