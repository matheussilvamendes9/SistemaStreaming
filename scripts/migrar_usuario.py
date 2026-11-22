"""Ajusta a tabela 'usuario' do banco LOCAL para o schema do contrato.

Uso (na raiz do projeto, com o venv ativo):
    python -m scripts.migrar_usuario

- Adiciona senha_hash e papel se ainda não existirem.
- Amplia 'nome' para VARCHAR(120).
- Idempotente e não apaga dados.
Obs.: o SQL oficial da branch main continua sendo a referência; este script
é só um atalho para quem já tem o banco antigo.
"""
from dotenv import load_dotenv

load_dotenv()

from database.connection import consultar, executar  # noqa: E402


def _colunas():
    linhas = consultar(
        "SELECT COLUMN_NAME AS coluna FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario'")
    return {l["coluna"].lower() for l in linhas}


def main():
    colunas = _colunas()
    if not colunas:
        print("Tabela 'usuario' não encontrada. Confira o banco configurado no .env.")
        return

    if "senha_hash" not in colunas:
        executar("ALTER TABLE usuario ADD COLUMN senha_hash VARCHAR(255) NULL AFTER email", ())
        print("+ coluna senha_hash adicionada")
    else:
        print("= senha_hash já existe")

    if "papel" not in colunas:
        executar(
            "ALTER TABLE usuario ADD COLUMN papel ENUM('admin','usuario') "
            "NOT NULL DEFAULT 'usuario' AFTER senha_hash", ())
        print("+ coluna papel adicionada")
    else:
        print("= papel já existe")

    executar("ALTER TABLE usuario MODIFY nome VARCHAR(120) NOT NULL", ())
    print("= nome ajustado para VARCHAR(120)")

    print("\nPronto. Agora rode: python -m scripts.criar_admin")


if __name__ == "__main__":
    main()
