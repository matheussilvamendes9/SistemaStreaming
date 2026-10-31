"""Erro unico da aplicacao: a interface (Streamlit) captura apenas este
e mostra a mensagem ao usuario com st.error(str(e))."""

class ErroAplicacao(Exception):
    pass