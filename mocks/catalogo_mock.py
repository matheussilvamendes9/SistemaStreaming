
# Dados fictícios para desenvolvimento do catálogo.
# Este arquivo simula as operações que futuramente serão
# realizadas pela API FastAPI.

GENEROS = [
    {"id_genero": 1, "nome": "Ação"},
    {"id_genero": 2, "nome": "Aventura"},
    {"id_genero": 3, "nome": "Animação"},
    {"id_genero": 4, "nome": "Comédia"},
    {"id_genero": 5, "nome": "Drama"},
    {"id_genero": 6, "nome": "Fantasia"},
    {"id_genero": 7, "nome": "Ficção Científica"},
    {"id_genero": 8, "nome": "Romance"},
    {"id_genero": 9, "nome": "Suspense"},
    {"id_genero": 10, "nome": "Terror"},
    {"id_genero": 11, "nome": "Documentário"},
    {"id_genero": 12, "nome": "Musical"},
]

CONTEUDOS = [
    {
        "id_conteudo": 1,
        "titulo": "Interestelar",
        "tipo": "filme",
        "ano_lancamento": 2014,
        "duracao_minutos": 169,
        "ids_generos": [2, 3],
    },
    {
        "id_conteudo": 2,
        "titulo": "Breaking Bad",
        "tipo": "serie",
        "ano_lancamento": 2008,
        "duracao_minutos": None,
        "ids_generos": [2, 4],
    },
    {
        "id_conteudo": 3,
        "titulo": "Oppenheimer",
        "tipo": "filme",
        "ano_lancamento": 2023,
        "duracao_minutos": 180,
        "ids_generos": [2],
    },
]

EPISODIOS = [
    {
        "id_episodio": 1,
        "id_serie": 2,
        "titulo": "Piloto",
        "temporada": 1,
        "episodio": 1,
        "duracao_minutos": 58,
    },
    {
        "id_episodio": 2,
        "id_serie": 2,
        "titulo": "O Gato na Bolsa",
        "temporada": 1,
        "episodio": 2,
        "duracao_minutos": 48,
    },
]

# ----------------------------------------------------
# GÊNEROS
# ----------------------------------------------------

def listar_generos():
    return [genero.copy() for genero in GENEROS]


# ----------------------------------------------------
# CONTEÚDOS
# ----------------------------------------------------

def listar_catalogo(busca=None, tipo=None):
    resultados = []

    for conteudo in CONTEUDOS:
        if busca and busca.lower() not in conteudo["titulo"].lower():
            continue

        if tipo and conteudo["tipo"] != tipo:
            continue

        item = conteudo.copy()

        item["generos"] = [
            genero["nome"]
            for genero in GENEROS
            if genero["id_genero"] in conteudo["ids_generos"]
        ]

        item["total_episodios"] = sum(
            episodio["id_serie"] == conteudo["id_conteudo"]
            for episodio in EPISODIOS
        )

        resultados.append(item)

    return resultados


def obter_conteudo(id_conteudo):
    for conteudo in CONTEUDOS:
        if conteudo["id_conteudo"] == id_conteudo:
            return conteudo.copy()

    raise ValueError("Conteúdo não encontrado.")


def criar_conteudo(
    titulo,
    tipo,
    ano_lancamento,
    duracao_minutos,
    ids_generos
):
    novo_id = max(
        [c["id_conteudo"] for c in CONTEUDOS],
        default=0
    ) + 1

    novo_conteudo = {
        "id_conteudo": novo_id,
        "titulo": titulo,
        "tipo": tipo,
        "ano_lancamento": ano_lancamento,
        "duracao_minutos": duracao_minutos,
        "ids_generos": list(ids_generos),
    }

    CONTEUDOS.append(novo_conteudo)


def atualizar_conteudo(
    id_conteudo,
    titulo,
    tipo,
    ano_lancamento,
    duracao_minutos,
    ids_generos
):
    for conteudo in CONTEUDOS:
        if conteudo["id_conteudo"] == id_conteudo:
            conteudo.update({
                "titulo": titulo,
                "tipo": tipo,
                "ano_lancamento": ano_lancamento,
                "duracao_minutos": duracao_minutos,
                "ids_generos": list(ids_generos),
            })
            return

    raise ValueError("Conteúdo não encontrado.")


def excluir_conteudo(id_conteudo):
    global CONTEUDOS, EPISODIOS

    if not any(
        c["id_conteudo"] == id_conteudo
        for c in CONTEUDOS
    ):
        raise ValueError("Conteúdo não encontrado.")

    CONTEUDOS = [
        c for c in CONTEUDOS
        if c["id_conteudo"] != id_conteudo
    ]

    EPISODIOS = [
        ep for ep in EPISODIOS
        if ep["id_serie"] != id_conteudo
    ]


# ----------------------------------------------------
# EPISÓDIOS
# ----------------------------------------------------

def listar_episodios(id_serie):
    return [
        ep.copy()
        for ep in EPISODIOS
        if ep["id_serie"] == id_serie
    ]


def obter_episodio(id_episodio):
    for episodio in EPISODIOS:
        if episodio["id_episodio"] == id_episodio:
            return episodio.copy()

    raise ValueError("Episódio não encontrado.")


def criar_episodio(
    id_serie,
    titulo,
    temporada,
    numero,
    duracao_minutos
):
    serie = obter_conteudo(id_serie)

    if serie["tipo"] != "serie":
        raise ValueError("Só é possível cadastrar episódios em séries.")

    novo_id = max(
        [ep["id_episodio"] for ep in EPISODIOS],
        default=0
    ) + 1

    EPISODIOS.append({
        "id_episodio": novo_id,
        "id_serie": id_serie,
        "titulo": titulo,
        "temporada": temporada,
        "episodio": numero,
        "duracao_minutos": duracao_minutos,
    })


def atualizar_episodio(
    id_episodio,
    titulo,
    temporada,
    numero,
    duracao_minutos
):
    for episodio in EPISODIOS:
        if episodio["id_episodio"] == id_episodio:
            episodio.update({
                "titulo": titulo,
                "temporada": temporada,
                "episodio": numero,
                "duracao_minutos": duracao_minutos,
            })
            return

    raise ValueError("Episódio não encontrado.")


def excluir_episodio(id_episodio):
    global EPISODIOS

    if not any(
        ep["id_episodio"] == id_episodio
        for ep in EPISODIOS
    ):
        raise ValueError("Episódio não encontrado.")

    EPISODIOS = [
        ep for ep in EPISODIOS
        if ep["id_episodio"] != id_episodio
    ]
