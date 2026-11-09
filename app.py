import streamlit as st
import pandas as pd
import altair as alt

from components.usuarios import mostrar_usuarios
from components.catalogo import mostrar_catalogo
from components.assinaturas import mostrar_assinaturas
from components.historico import mostrar_historico
from components.analise import mostrar_analise

from services.indicadores_service import obter_indicadores
from database.erros import ErroAplicacao


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="StreamHub | Administração",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PALETA
# ============================================================

COR_PRIMARIA = "#E50914"
COR_FUNDO = "#0E1117"
COR_SUPERFICIE = "#171B26"
COR_SUPERFICIE_2 = "#1E2331"
COR_BORDA = "#2A3042"
COR_TEXTO = "#F5F6F8"
COR_TEXTO_SUAVE = "#9AA3B5"


# ============================================================
# ESTILIZAÇÃO GLOBAL
# ============================================================

st.markdown(f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', sans-serif;
}}

/* Área principal */
.block-container {{
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}}

/* Esconde elementos padrão do Streamlit */
#MainMenu, footer {{
    visibility: hidden;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

/* ---------- Barra lateral ---------- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #131722 0%, #0F121B 100%);
    border-right: 1px solid {COR_BORDA};
}}

[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1.5rem;
}}

.marca {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 4px 0 4px;
}}

.marca-icone {{
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, {COR_PRIMARIA}, #9B0A12);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    box-shadow: 0 6px 18px rgba(229, 9, 20, 0.35);
}}

.marca-nome {{
    font-size: 20px;
    font-weight: 800;
    color: {COR_TEXTO};
    line-height: 1.1;
}}

.marca-sub {{
    font-size: 12px;
    color: {COR_TEXTO_SUAVE};
}}

.rotulo-menu {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: {COR_TEXTO_SUAVE};
    margin: 8px 0 6px 4px;
}}

/* Menu de navegação (radio estilizado como itens de menu) */
[data-testid="stSidebar"] [role="radiogroup"] {{
    gap: 4px;
}}

[data-testid="stSidebar"] [role="radiogroup"] label {{
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid transparent;
    width: 100%;
    cursor: pointer;
    transition: all 0.15s ease;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background-color: {COR_SUPERFICIE_2};
}}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
    background: linear-gradient(90deg, rgba(229,9,20,0.18), rgba(229,9,20,0.04));
    border-color: rgba(229, 9, 20, 0.45);
}}

[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{
    display: none;
}}

[data-testid="stSidebar"] [role="radiogroup"] label p {{
    font-weight: 600;
    font-size: 15px;
}}

/* ---------- Títulos ---------- */
h1, h2, h3 {{
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}}

/* ---------- Cabeçalho da página ---------- */
.hero {{
    position: relative;
    overflow: hidden;
    padding: 32px 36px;
    border-radius: 20px;
    border: 1px solid {COR_BORDA};
    background:
        radial-gradient(circle at 90% 0%, rgba(229, 9, 20, 0.28), transparent 45%),
        linear-gradient(135deg, {COR_SUPERFICIE} 0%, #121521 100%);
    margin-bottom: 28px;
}}

.hero-tag {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: {COR_PRIMARIA};
    background: rgba(229, 9, 20, 0.12);
    border: 1px solid rgba(229, 9, 20, 0.35);
    padding: 5px 12px;
    border-radius: 999px;
    margin-bottom: 14px;
}}

.hero-titulo {{
    font-size: 38px;
    font-weight: 800;
    color: {COR_TEXTO};
    margin: 0 0 6px 0;
    letter-spacing: -0.03em;
}}

.hero-texto {{
    font-size: 16px;
    color: {COR_TEXTO_SUAVE};
    margin: 0;
    max-width: 640px;
}}

/* ---------- Cartões de indicadores ---------- */
.kpi {{
    position: relative;
    overflow: hidden;
    background: {COR_SUPERFICIE};
    border: 1px solid {COR_BORDA};
    border-radius: 16px;
    padding: 22px 22px 20px 22px;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}}

.kpi:hover {{
    transform: translateY(-3px);
    border-color: rgba(229, 9, 20, 0.5);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
}}

.kpi::before {{
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, {COR_PRIMARIA}, transparent);
}}

.kpi-topo {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}}

.kpi-rotulo {{
    font-size: 13px;
    font-weight: 600;
    color: {COR_TEXTO_SUAVE};
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

.kpi-icone {{
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: rgba(229, 9, 20, 0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}}

.kpi-valor {{
    font-size: 36px;
    font-weight: 800;
    color: {COR_TEXTO};
    line-height: 1.1;
    letter-spacing: -0.02em;
}}

.kpi-detalhe {{
    margin-top: 8px;
    font-size: 13px;
    color: {COR_TEXTO_SUAVE};
}}

/* ---------- Seções ---------- */
.secao-titulo {{
    font-size: 22px;
    font-weight: 800;
    color: {COR_TEXTO};
    margin: 0;
}}

.secao-sub {{
    font-size: 14px;
    color: {COR_TEXTO_SUAVE};
    margin: 2px 0 14px 0;
}}

/* Containers com borda */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 16px !important;
    border-color: {COR_BORDA} !important;
    background-color: {COR_SUPERFICIE};
}}

/* ---------- Ranking ---------- */
.rank-item {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 14px;
    border-radius: 12px;
    background: {COR_SUPERFICIE_2};
    border: 1px solid transparent;
    margin-bottom: 8px;
    transition: border-color 0.15s ease;
}}

.rank-item:hover {{
    border-color: rgba(229, 9, 20, 0.4);
}}

.rank-pos {{
    min-width: 32px;
    height: 32px;
    border-radius: 9px;
    background: rgba(229, 9, 20, 0.14);
    color: {COR_PRIMARIA};
    font-weight: 800;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.rank-nome {{
    flex: 1;
    font-weight: 600;
    color: {COR_TEXTO};
    font-size: 14px;
}}

.rank-valor {{
    font-weight: 700;
    color: {COR_TEXTO_SUAVE};
    font-size: 13px;
}}

/* ---------- Componentes gerais ---------- */
.stButton > button {{
    border-radius: 10px;
    font-weight: 600;
    padding: 0.5rem 1.1rem;
    transition: all 0.2s ease;
}}

.stButton > button:hover {{
    border-color: {COR_PRIMARIA};
    color: {COR_PRIMARIA};
    transform: translateY(-1px);
}}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {{
    border-radius: 10px;
}}

[data-testid="stAlert"] {{
    border-radius: 12px;
}}

[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
}}

hr {{
    border-color: {COR_BORDA};
}}

</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNÇÕES AUXILIARES DE INTERFACE
# ============================================================

def formatar_numero(valor):
    """Formata inteiros no padrão brasileiro (1.234)."""
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


# ============================================================
# BARRA LATERAL
# ============================================================

with st.sidebar:

    st.markdown("""
    <div class="marca">
        <div class="marca-icone">🎬</div>
        <div>
            <div class="marca-nome">StreamHub</div>
            <div class="marca-sub">Painel administrativo</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.divider()

    st.markdown('<div class="rotulo-menu">NAVEGAÇÃO</div>', unsafe_allow_html=True)

    pagina = st.radio(
        "Menu principal",
        [
            "Visão geral",
            "Usuários",
            "Catálogo",
            "Assinaturas",
            "Histórico",
            "Análise de Dados"
        ],
        format_func=lambda p: {
            "Visão geral": "📊  Visão geral",
            "Usuários": "👥  Usuários",
            "Catálogo": "🎞️  Catálogo",
            "Assinaturas": "💳  Assinaturas",
            "Histórico": "🕒  Histórico",
            "Análise de Dados": "📈  Análise de Dados",
        }[p],
        label_visibility="collapsed"
    )

    st.divider()

    st.caption("Sistema de gerenciamento")
    st.caption("Projeto acadêmico • 2026")


# ============================================================
# VISÃO GERAL
# ============================================================

if pagina == "Visão geral":

    cabecalho_pagina(
        "PAINEL ADMINISTRATIVO",
        "Visão geral",
        "Bem-vindo ao StreamHub! Acompanhe os principais "
        "indicadores da plataforma em tempo real."
    )

    try:

        indicadores = obter_indicadores()

        total_conteudos = (
            indicadores["total_filmes"]
            + indicadores["total_series"]
        )

        # ----------------------------------------------------
        # INDICADORES
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4, gap="medium")

        with col1:
            cartao_indicador(
                "👥",
                "Usuários",
                formatar_numero(indicadores["total_usuarios"]),
                "Total de usuários registrados"
            )

        with col2:
            cartao_indicador(
                "🎬",
                "Conteúdos",
                formatar_numero(total_conteudos),
                f'{formatar_numero(indicadores["total_filmes"])} filmes · '
                f'{formatar_numero(indicadores["total_series"])} séries'
            )

        with col3:
            cartao_indicador(
                "▶️",
                "Reproduções",
                formatar_numero(indicadores["total_reproducoes"]),
                "Total de reproduções registradas"
            )

        with col4:
            cartao_indicador(
                "💳",
                "Assinaturas ativas",
                formatar_numero(indicadores["assinaturas_ativas"]),
                "Assinaturas atualmente ativas"
            )

        st.write("")
        st.write("")

        # ----------------------------------------------------
        # RANKING
        # ----------------------------------------------------

        top_conteudos = indicadores["top_conteudos"]

        titulo_secao(
            "Conteúdos mais reproduzidos",
            "Ranking dos conteúdos com maior número de reproduções."
        )

        if top_conteudos:

            df = pd.DataFrame(top_conteudos)

            df = df.rename(columns={
                "titulo": "Conteúdo",
                "total_reproducoes": "Reproduções"
            })

            df = df[["Conteúdo", "Reproduções"]]
            df = df.sort_values("Reproduções", ascending=False)

            col_grafico, col_lista = st.columns([3, 2], gap="large")

            with col_grafico:

                with st.container(border=True):

                    grafico = (
                        alt.Chart(df)
                        .mark_bar(
                            cornerRadiusTopRight=8,
                            cornerRadiusBottomRight=8,
                            color=COR_PRIMARIA,
                            size=22
                        )
                        .encode(
                            x=alt.X(
                                "Reproduções:Q",
                                title=None,
                                axis=alt.Axis(
                                    grid=True,
                                    gridColor=COR_BORDA,
                                    labelColor=COR_TEXTO_SUAVE,
                                    domain=False,
                                    tickMinStep=1
                                )
                            ),
                            y=alt.Y(
                                "Conteúdo:N",
                                sort="-x",
                                title=None,
                                axis=alt.Axis(
                                    labelColor=COR_TEXTO,
                                    labelLimit=220,
                                    domain=False,
                                    ticks=False
                                )
                            ),
                            tooltip=["Conteúdo", "Reproduções"]
                        )
                        .properties(height=max(260, 48 * len(df)))
                        .configure(background="transparent")
                        .configure_view(strokeWidth=0)
                    )

                    st.altair_chart(grafico, use_container_width=True)

            with col_lista:

                with st.container(border=True):

                    st.markdown("**🏆 Top conteúdos**")

                    for posicao, linha in enumerate(
                        df.itertuples(index=False), start=1
                    ):
                        st.markdown(f"""
                        <div class="rank-item">
                            <div class="rank-pos">{posicao}</div>
                            <div class="rank-nome">{linha[0]}</div>
                            <div class="rank-valor">
                                {formatar_numero(linha[1])} ▶
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        else:

            st.info(
                "Ainda não existem conteúdos cadastrados."
            )

    except ErroAplicacao as e:

        st.error(str(e))

    except Exception as e:

        st.error(
            f"Não foi possível carregar a visão geral: {e}"
        )


# ============================================================
# DEMAIS PÁGINAS
# ============================================================

elif pagina == "Usuários":

    mostrar_usuarios()

elif pagina == "Catálogo":

    mostrar_catalogo()

elif pagina == "Assinaturas":

    mostrar_assinaturas()

elif pagina == "Histórico":

    mostrar_historico()

elif pagina == "Análise de Dados":

    mostrar_analise()