
USUARIO_ADMIN = {
    "id_usuario": 1,
    "nome": "Administrador",
    "email": "admin@streamhub.com",
    "papel": "admin"
}

USUARIO_COMUM = {
    "id_usuario": 2,
    "nome": "Usuário de Teste",
    "email": "usuario@streamhub.com",
    "papel": "usuario"
}

CONTEUDOS = [
    {
        "id_conteudo": 1,
        "titulo": "Interestelar",
        "tipo": "filme",
        "ano_lancamento": 2014,
        "duracao_minutos": 169,
        "generos": ["Ficção Científica", "Drama"]
    },
    {
        "id_conteudo": 2,
        "titulo": "Breaking Bad",
        "tipo": "serie",
        "ano_lancamento": 2008,
        "duracao_minutos": None,
        "generos": ["Drama", "Suspense"]
    }
]

PLANOS = [
    {"id_plano": 1, "nome": "basico", "valor": 20.00},
    {"id_plano": 2, "nome": "padrao", "valor": 35.00},
    {"id_plano": 3, "nome": "premium", "valor": 50.00}
]
