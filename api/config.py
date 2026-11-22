"""Configuração da API (tudo vem de variáveis de ambiente / .env)."""
import os

from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_MINUTOS = int(os.getenv("JWT_EXPIRA_MINUTOS", "60"))
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
    if o.strip()
]


def validar_configuracao():
    """Falha cedo se o segredo do JWT não estiver configurado."""
    if len(JWT_SECRET) < 32:
        raise RuntimeError(
            "Defina JWT_SECRET no .env com pelo menos 32 caracteres. "
            'Gere um com: python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
