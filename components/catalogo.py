import streamlit as st
import pandas as pd

from services.conteudo_service import (
    listar_catalogo,
    obter_conteudo,
    criar_conteudo,
    atualizar_conteudo,
    excluir_conteudo
)

from services.genero_service import listar_generos

from services.episodio_service import (
    listar_episodios,
    obter_episodio,
    criar_episodio,
    atualizar_episodio,
    excluir_episodio
)

from database.erros import ErroAplicacao



# FUNÇÕES AUXILIARES DE INTERFACE
# (as classes CSS são definidas no app.py)


def formatar_numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


def cabecalho_pagina(tag, titulo, texto):
    st.markdown(f"""
    <div class="hero">
        <span class="hero-tag">{tag}</span>
        <h1 class="hero-titulo">{titulo}</h1>
        <p class="hero-texto">{texto}</p>
    </div>
    """, unsafe_allow_html=True)


def cartao_indicador(icone, rotulo, valor, detalhe):
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-topo">
            <span class="kpi-rotulo">{rotulo}</span>
            <span class="kpi-icone">{icone}</span>
        </div>
        <div class="kpi-valor">{valor}</div>
        <div class="kpi-detalhe">{detalhe}</div>
    </div>
    """, unsafe_allow_html=True)


def titulo_secao(titulo, subtitulo):
    st.markdown(f"""
    <p class="secao-titulo">{titulo}</p>
    <p class="secao-sub">{subtitulo}</p>
    """, unsafe_allow_html=True)



# PÁGINA


def mostrar_catalogo():

    cabecalho_pagina(
        "GESTÃO",
        "Catálogo",
        "Cadastre, consulte, edite e exclua filmes, séries e episódios."
    )

    try:
        generos = listar_generos()
        conteudos = listar_catalogo()

    except Exception as e:
        st.error(f"Erro ao carregar o catálogo: {e}")
        return

    
    # Indicadores
    
    total = len(conteudos)
    filmes = sum(c["tipo"] == "filme" for c in conteudos)
    series = sum(c["tipo"] == "serie" for c in conteudos)
    episodios_total = sum(c.get("total_episodios", 0) for c in conteudos)

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        cartao_indicador(
            "🎬", "Conteúdos",
            formatar_numero(total),
            "Filmes e séries no catálogo"
        )

    with col2:
        cartao_indicador(
            "🍿", "Filmes",
            formatar_numero(filmes),
            "Títulos do tipo filme"
        )

    with col3:
        cartao_indicador(
            "📺", "Séries",
            formatar_numero(series),
            "Títulos do tipo série"
        )

    with col4:
        cartao_indicador(
            "🎞️", "Episódios",
            formatar_numero(episodios_total),
            "Episódios cadastrados"
        )

    st.write("")
    st.write("")

    
    # Dados auxiliares
    
    nomes_generos = [g["nome"] for g in generos]
    mapa_generos = {g["nome"]: g["id_genero"] for g in generos}

    opcoes = {
        f'{c["titulo"]} (ID: {c["id_conteudo"]})': c["id_conteudo"]
        for c in conteudos
    }

    
    # Seções principais
    
    aba_conteudos, aba_episodios = st.tabs([
        "Conteúdos",
        "Episódios"
    ])

    # ========================================================
    # CONTEÚDOS
    # ========================================================
    with aba_conteudos:

        titulo_secao(
            "Conteúdos cadastrados",
            "Pesquise por título ou filtre por tipo."
        )

        with st.container(border=True):

            col_busca, col_filtro = st.columns([3, 1], gap="medium")

            with col_busca:
                busca = st.text_input(
                    "Pesquisar por título",
                    placeholder="🔍  Digite o nome do conteúdo..."
                )

            with col_filtro:
                tipo_filtro = st.selectbox(
                    "Filtrar por tipo",
                    ["Todos", "Filme", "Série"]
                )

            tipo_db = {
                "Todos": None,
                "Filme": "filme",
                "Série": "serie"
            }[tipo_filtro]

            try:
                filtrados = listar_catalogo(
                    busca=busca,
                    tipo=tipo_db
                )

            except Exception as e:
                st.error(f"Erro ao consultar conteúdos: {e}")
                return

            if filtrados:
                df = pd.DataFrame(filtrados)

                df = df.rename(columns={
                    "id_conteudo": "ID",
                    "titulo": "Título",
                    "tipo": "Tipo",
                    "ano_lancamento": "Ano",
                    "duracao_minutos": "Duração (min)",
                    "generos": "Gêneros",
                    "total_episodios": "Episódios"
                })

                df["Tipo"] = df["Tipo"].map({
                    "filme": "🍿 Filme",
                    "serie": "📺 Série"
                })

                st.caption(
                    f"{formatar_numero(len(df))} "
                    f"{'resultado' if len(df) == 1 else 'resultados'}"
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info("Nenhum conteúdo encontrado.")

        st.write("")

        titulo_secao(
            "Ações",
            "Cadastre, edite ou exclua filmes e séries."
        )

        aba_cad, aba_edit, aba_exc = st.tabs([
            "Cadastrar",
            "Editar",
            "Excluir"
        ])

        
        # Cadastro de conteúdo
        
        with aba_cad:

            with st.container(border=True):

                st.markdown("**Cadastrar conteúdo**")

                with st.form(
                    "form_cadastro_conteudo",
                    clear_on_submit=True,
                    border=False
                ):

                    titulo = st.text_input("Título")

                    col_tipo, col_ano = st.columns(2, gap="medium")

                    with col_tipo:
                        tipo = st.selectbox(
                            "Tipo de conteúdo",
                            ["Filme", "Série"],
                            key="cadastro_tipo"
                        )

                    with col_ano:
                        ano = st.number_input(
                            "Ano de lançamento",
                            min_value=1888,
                            max_value=2100,
                            value=2020,
                            step=1,
                            key="cadastro_ano"
                        )

                    duracao = st.number_input(
                        "Duração em minutos (obrigatória para filmes)",
                        min_value=0,
                        max_value=10000,
                        value=0,
                        step=1,
                        help="Para séries, deixe 0. A duração será informada nos episódios."
                    )

                    generos_selecionados = st.multiselect(
                        "Gêneros",
                        options=nomes_generos
                    )

                    cadastrar = st.form_submit_button(
                        "Cadastrar conteúdo",
                        use_container_width=True,
                        type="primary"
                    )

                    if cadastrar:

                        if not titulo.strip():
                            st.error("Informe o título do conteúdo.")

                        elif tipo == "Filme" and duracao <= 0:
                            st.error("Informe a duração do filme.")

                        elif not generos:
                            st.error("Não existem gêneros cadastrados no banco.")

                        else:
                            try:
                                ids = [
                                    mapa_generos[nome]
                                    for nome in generos_selecionados
                                ]

                                criar_conteudo(
                                    titulo=titulo,
                                    tipo="filme" if tipo == "Filme" else "serie",
                                    ano_lancamento=int(ano),
                                    duracao_minutos=int(duracao) if duracao > 0 else None,
                                    ids_generos=ids
                                )

                                st.success("Conteúdo cadastrado com sucesso!")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Erro ao cadastrar conteúdo: {e}")

        
        # Edição de conteúdo
        
        with aba_edit:

            if conteudos:

                with st.container(border=True):

                    st.markdown("**Editar conteúdo**")

                    selecionado = st.selectbox(
                        "Selecione o conteúdo",
                        list(opcoes.keys()),
                        key="conteudo_editar"
                    )

                    id_editar = opcoes[selecionado]
                    conteudo = obter_conteudo(id_editar)

                    tipo_atual = conteudo["tipo"]
                    duracao_atual = conteudo["duracao_minutos"] or 0

                    generos_atuais = [
                        g["nome"]
                        for g in generos
                        if g["id_genero"] in conteudo["ids_generos"]
                    ]

                    with st.form("form_edicao_conteudo", border=False):

                        novo_titulo = st.text_input(
                            "Título",
                            value=conteudo["titulo"]
                        )

                        col_tipo, col_ano = st.columns(2, gap="medium")

                        with col_tipo:
                            novo_tipo = st.selectbox(
                                "Tipo",
                                ["Filme", "Série"],
                                index=0 if tipo_atual == "filme" else 1
                            )

                        with col_ano:
                            novo_ano = st.number_input(
                                "Ano de lançamento",
                                min_value=1888,
                                max_value=2100,
                                value=int(conteudo["ano_lancamento"]),
                                step=1
                            )

                        nova_duracao = st.number_input(
                            "Duração em minutos (obrigatória para filmes)",
                            min_value=0,
                            max_value=10000,
                            value=int(duracao_atual),
                            step=1
                        )

                        novos_generos = st.multiselect(
                            "Gêneros",
                            options=nomes_generos,
                            default=generos_atuais
                        )

                        salvar = st.form_submit_button(
                            "Salvar alterações",
                            use_container_width=True,
                            type="primary"
                        )

                        if salvar:

                            if not novo_titulo.strip():
                                st.error("Informe o título do conteúdo.")

                            elif novo_tipo == "Filme" and nova_duracao <= 0:
                                st.error("Informe a duração do filme.")

                            else:
                                try:
                                    ids = [
                                        mapa_generos[nome]
                                        for nome in novos_generos
                                    ]

                                    atualizar_conteudo(
                                        id_conteudo=id_editar,
                                        titulo=novo_titulo,
                                        tipo="filme" if novo_tipo == "Filme" else "serie",
                                        ano_lancamento=int(novo_ano),
                                        duracao_minutos=int(nova_duracao) if nova_duracao > 0 else None,
                                        ids_generos=ids
                                    )

                                    st.success("Conteúdo atualizado com sucesso!")
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Erro ao atualizar conteúdo: {e}")

            else:
                st.info("Não existem conteúdos para editar.")

        
        # Exclusão de conteúdo
        
        with aba_exc:

            if conteudos:

                with st.container(border=True):

                    st.markdown("**Excluir conteúdo**")

                    st.warning(
                        "Esta ação não pode ser desfeita.",
                        icon="⚠️"
                    )

                    conteudo_excluir = st.selectbox(
                        "Selecione o conteúdo que deseja excluir",
                        list(opcoes.keys()),
                        key="conteudo_excluir"
                    )

                    id_excluir = opcoes[conteudo_excluir]

                    confirmar = st.checkbox(
                        "Confirmo que desejo excluir este conteúdo.",
                        key="confirmar_exclusao_conteudo"
                    )

                    if st.button(
                        "Excluir conteúdo",
                        use_container_width=True,
                        type="primary"
                    ):

                        if confirmar:
                            try:
                                excluir_conteudo(id_excluir)

                                st.success("Conteúdo excluído com sucesso!")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Erro ao excluir conteúdo: {e}")

                        else:
                            st.warning("Confirme a exclusão antes de continuar.")

            else:
                st.info("Não existem conteúdos para excluir.")

    # ========================================================
    # EPISÓDIOS
    # ========================================================
    with aba_episodios:

        series_cadastradas = [
            c for c in conteudos if c["tipo"] == "serie"
        ]

        if not series_cadastradas:

            st.info(
                "Cadastre uma série no catálogo antes de gerenciar episódios."
            )

        else:

            opcoes_series = {
                f'{s["titulo"]} (ID: {s["id_conteudo"]})': s["id_conteudo"]
                for s in series_cadastradas
            }

            titulo_secao(
                "Episódios da série",
                "Selecione uma série para consultar e gerenciar seus episódios."
            )

            with st.container(border=True):

                serie_selecionada = st.selectbox(
                    "Selecione a série",
                    list(opcoes_series.keys()),
                    key="serie_episodios"
                )

                id_serie = opcoes_series[serie_selecionada]

                try:
                    episodios = listar_episodios(id_serie)

                except Exception as e:
                    st.error(f"Erro ao carregar episódios: {e}")
                    return

                if episodios:

                    df_ep = pd.DataFrame(episodios)

                    df_ep = df_ep.rename(columns={
                        "id_episodio": "ID",
                        "titulo": "Título",
                        "temporada": "Temporada",
                        "episodio": "Episódio",
                        "duracao_minutos": "Duração (min)"
                    })

                    colunas = [
                        "ID", "Título", "Temporada",
                        "Episódio", "Duração (min)"
                    ]

                    st.caption(
                        f"{formatar_numero(len(df_ep))} "
                        f"{'episódio' if len(df_ep) == 1 else 'episódios'}"
                    )

                    st.dataframe(
                        df_ep[colunas],
                        use_container_width=True,
                        hide_index=True
                    )

                else:
                    st.info("Esta série ainda não possui episódios.")

            st.write("")

            opcoes_episodios = {
                f'T{ep["temporada"]}E{ep["episodio"]} - {ep["titulo"]} (ID: {ep["id_episodio"]})':
                ep["id_episodio"]
                for ep in episodios
            }

            titulo_secao(
                "Ações",
                "Cadastre, edite ou exclua episódios da série selecionada."
            )

            aba_cad_ep, aba_edit_ep, aba_exc_ep = st.tabs([
                "Cadastrar",
                "Editar",
                "Excluir"
            ])

            # 
            # Cadastro de episódio
            # 
            with aba_cad_ep:

                with st.container(border=True):

                    st.markdown("**Cadastrar episódio**")

                    with st.form(
                        "form_cadastro_episodio",
                        clear_on_submit=True,
                        border=False
                    ):

                        titulo_ep = st.text_input("Título do episódio")

                        col_temp, col_num, col_dur = st.columns(3, gap="medium")

                        with col_temp:
                            temporada = st.number_input(
                                "Temporada",
                                min_value=1,
                                value=1,
                                step=1
                            )

                        with col_num:
                            numero = st.number_input(
                                "Número do episódio",
                                min_value=1,
                                value=1,
                                step=1
                            )

                        with col_dur:
                            duracao_ep = st.number_input(
                                "Duração em minutos",
                                min_value=1,
                                value=40,
                                step=1
                            )

                        cadastrar_ep = st.form_submit_button(
                            "Cadastrar episódio",
                            use_container_width=True,
                            type="primary"
                        )

                        if cadastrar_ep:

                            if not titulo_ep.strip():
                                st.error("Informe o título do episódio.")

                            else:
                                try:
                                    criar_episodio(
                                        id_serie=id_serie,
                                        titulo=titulo_ep,
                                        temporada=int(temporada),
                                        numero=int(numero),
                                        duracao_minutos=int(duracao_ep)
                                    )

                                    st.success("Episódio cadastrado com sucesso!")
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Erro ao cadastrar episódio: {e}")

            # 
            # Edição de episódio
            # 
            with aba_edit_ep:

                if episodios:

                    with st.container(border=True):

                        st.markdown("**Editar episódio**")

                        ep_selecionado = st.selectbox(
                            "Selecione o episódio para editar",
                            list(opcoes_episodios.keys()),
                            key="episodio_editar"
                        )

                        id_ep_editar = opcoes_episodios[ep_selecionado]
                        episodio_atual = obter_episodio(id_ep_editar)

                        with st.form("form_edicao_episodio", border=False):

                            novo_titulo_ep = st.text_input(
                                "Título do episódio",
                                value=episodio_atual["titulo"]
                            )

                            col_temp, col_num, col_dur = st.columns(3, gap="medium")

                            with col_temp:
                                nova_temporada = st.number_input(
                                    "Temporada",
                                    min_value=1,
                                    value=int(episodio_atual["temporada"]),
                                    step=1
                                )

                            with col_num:
                                novo_numero = st.number_input(
                                    "Número do episódio",
                                    min_value=1,
                                    value=int(episodio_atual["episodio"]),
                                    step=1
                                )

                            with col_dur:
                                nova_duracao_ep = st.number_input(
                                    "Duração em minutos",
                                    min_value=1,
                                    value=int(episodio_atual["duracao_minutos"]),
                                    step=1
                                )

                            salvar_ep = st.form_submit_button(
                                "Salvar alterações do episódio",
                                use_container_width=True,
                                type="primary"
                            )

                            if salvar_ep:

                                if not novo_titulo_ep.strip():
                                    st.error("Informe o título do episódio.")

                                else:
                                    try:
                                        atualizar_episodio(
                                            id_episodio=id_ep_editar,
                                            titulo=novo_titulo_ep,
                                            temporada=int(nova_temporada),
                                            numero=int(novo_numero),
                                            duracao_minutos=int(nova_duracao_ep)
                                        )

                                        st.success("Episódio atualizado com sucesso!")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Erro ao atualizar episódio: {e}")

                else:
                    st.info("Cadastre um episódio para habilitar a edição.")

            # 
            # Exclusão de episódio
            # 
            with aba_exc_ep:

                if episodios:

                    with st.container(border=True):

                        st.markdown("**Excluir episódio**")

                        st.warning(
                            "Esta ação não pode ser desfeita.",
                            icon="⚠️"
                        )

                        ep_excluir = st.selectbox(
                            "Selecione o episódio que deseja excluir",
                            list(opcoes_episodios.keys()),
                            key="episodio_excluir"
                        )

                        id_ep_excluir = opcoes_episodios[ep_excluir]

                        confirmar_ep = st.checkbox(
                            "Confirmo que desejo excluir este episódio.",
                            key="confirmar_exclusao_episodio"
                        )

                        if st.button(
                            "Excluir episódio",
                            use_container_width=True,
                            type="primary"
                        ):

                            if confirmar_ep:
                                try:
                                    excluir_episodio(id_ep_excluir)

                                    st.success("Episódio excluído com sucesso!")
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Erro ao excluir episódio: {e}")

                            else:
                                st.warning("Confirme a exclusão antes de continuar.")

                else:
                    st.info("Não existem episódios para excluir.")