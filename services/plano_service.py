"""CRUD de planos (tabela 'plano', usada pelas assinaturas - RF04)."""
from database.connection import consultar, executar
from database.erros import ErroAplicacao
from services.validators import exigir_texto, validar_valor_monetario


def listar_planos():
    return consultar("""
        SELECT p.id_plano, p.nome, p.valor, COUNT(a.id_assinatura) AS total_assinaturas
        FROM plano p
        LEFT JOIN assinatura a ON a.id_plano = p.id_plano
        GROUP BY p.id_plano, p.nome, p.valor
        ORDER BY p.valor, p.nome
    """)


def obter_plano(id_plano):
    r = consultar("SELECT id_plano, nome, valor FROM plano WHERE id_plano = %s", (id_plano,))
    return r[0] if r else None


def criar_plano(nome, valor):
    nome = exigir_texto(nome, "nome do plano", 50).lower()
    valor = validar_valor_monetario(valor)
    return executar("INSERT INTO plano (nome, valor) VALUES (%s, %s)", (nome, valor))


def atualizar_plano(id_plano, nome, valor):
    """Nao altera o valor das assinaturas ja existentes (ficam com o preco da epoca)."""
    nome = exigir_texto(nome, "nome do plano", 50).lower()
    valor = validar_valor_monetario(valor)
    executar("UPDATE plano SET nome = %s, valor = %s WHERE id_plano = %s",
             (nome, valor, id_plano))


def excluir_plano(id_plano):
    """O banco impede excluir plano que ainda tem assinaturas (RESTRICT)."""
    if not obter_plano(id_plano):
        raise ErroAplicacao("Plano nao encontrado.")
    executar("DELETE FROM plano WHERE id_plano = %s", (id_plano,))