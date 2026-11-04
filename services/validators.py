"""Validacoes reutilizaveis (RNF05)."""
import math
import re
from datetime import date, datetime

from database.erros import ErroAplicacao

_EMAIL_REGEX = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


def exigir_texto(valor, campo, max_len=None):
    texto = (valor or "").strip()
    if not texto:
        raise ErroAplicacao(f"O campo '{campo}' e obrigatorio.")
    if max_len and len(texto) > max_len:
        raise ErroAplicacao(f"O campo '{campo}' aceita no maximo {max_len} caracteres.")
    return texto


def validar_email(email):
    email = exigir_texto(email, "e-mail", 255).lower()
    if not _EMAIL_REGEX.match(email):
        raise ErroAplicacao("Formato de e-mail invalido.")
    return email


def validar_inteiro(valor, campo, minimo=None, maximo=None):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ErroAplicacao(f"O campo '{campo}' deve ser um numero inteiro.")
    if minimo is not None and numero < minimo:
        raise ErroAplicacao(f"O campo '{campo}' deve ser no minimo {minimo}.")
    if maximo is not None and numero > maximo:
        raise ErroAplicacao(f"O campo '{campo}' deve ser no maximo {maximo}.")
    return numero


def validar_decimal(valor, campo, minimo=None):
    """Numero com ate 2 casas decimais (ex.: progresso em minutos)."""
    try:
        numero = round(float(valor), 2)
    except (TypeError, ValueError):
        raise ErroAplicacao(f"O campo '{campo}' deve ser numerico.")
    if not math.isfinite(numero):
        raise ErroAplicacao(f"O campo '{campo}' deve ser numerico.")
    if minimo is not None and numero < minimo:
        raise ErroAplicacao(f"O campo '{campo}' deve ser no minimo {minimo}.")
    return numero


def validar_valor_monetario(valor, campo="valor"):
    """Valor em reais; o banco exige valor maior que zero."""
    numero = validar_decimal(valor, campo)
    if numero <= 0:
        raise ErroAplicacao(f"O campo '{campo}' deve ser maior que zero.")
    return numero


def validar_opcao(valor, opcoes, campo):
    valor = (valor or "").strip().lower()
    if valor not in opcoes:
        raise ErroAplicacao(f"'{campo}' invalido. Opcoes: {', '.join(opcoes)}.")
    return valor


def validar_data(valor, campo, obrigatoria=True):
    if valor in (None, ""):
        if obrigatoria:
            raise ErroAplicacao(f"O campo '{campo}' e obrigatorio.")
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor), "%Y-%m-%d").date()
    except ValueError:
        raise ErroAplicacao(f"Data invalida em '{campo}' (use AAAA-MM-DD).")