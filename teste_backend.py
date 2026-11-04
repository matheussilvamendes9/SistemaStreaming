"""Teste do backend contra o banco real (streaming_db).
Rode na raiz do projeto:  python teste_backend.py
Cria dados com nomes unicos e APAGA tudo no final."""
import uuid
from datetime import date

from database.erros import ErroAplicacao
from services.assinatura_service import (criar_assinatura, encerrar_assinatura,
                                         listar_assinaturas)
from services.conteudo_service import criar_conteudo, excluir_conteudo, listar_catalogo
from services.episodio_service import criar_episodio, listar_episodios
from services.genero_service import criar_genero, excluir_genero
from services.historico_service import listar_historico, registrar_reproducao
from services.indicadores_service import obter_indicadores
from services.plano_service import criar_plano, excluir_plano, listar_planos
from services.usuario_service import criar_usuario, excluir_usuario

falhas = []


def esperar_erro(descricao, funcao):
    """Executa algo que DEVE gerar ErroAplicacao."""
    try:
        funcao()
    except ErroAplicacao as e:
        print(f"  [OK] {descricao} -> {e}")
    else:
        print(f"  [FALHA] {descricao}: deveria ter dado erro")
        falhas.append(descricao)


def main():
    s = uuid.uuid4().hex[:8]
    ids = {}
    try:
        print("1) Cadastros")
        ids["usuario"] = criar_usuario("Usuario Teste", f"teste_{s}@example.com")
        ids["genero"] = criar_genero(f"GeneroTeste{s}")
        ids["filme"] = criar_conteudo(f"Filme {s}", "filme", 2024, 120, [ids["genero"]])
        # serie: a duracao informada e ignorada (o banco exige NULL)
        ids["serie"] = criar_conteudo(f"Serie {s}", "serie", 2024, 999, [ids["genero"]])
        ids["episodio"] = criar_episodio(ids["serie"], "Piloto", 1, 1, 42)
        plano = listar_planos()[0]
        ids["assinatura"] = criar_assinatura(ids["usuario"], plano["id_plano"], date.today())
        print("  [OK] usuario, genero, filme, serie, episodio e assinatura criados")

        print("2) Historico")
        registrar_reproducao(ids["usuario"], ids["filme"], 90)
        registrar_reproducao(ids["usuario"], ids["serie"], 20.5, id_episodio=ids["episodio"])
        print("  [OK] reproducao de filme e de serie registradas")

        print("3) Consultas")
        cat = [c for c in listar_catalogo(busca=s)]
        print("  Catalogo:", [(c["titulo"], c["tipo"], c["duracao_minutos"],
                               c["generos"], c["total_episodios"]) for c in cat])
        print("  Episodios:", [(e["serie"], e["temporada"], e["episodio"]) for e in listar_episodios(ids["serie"])])
        print("  Assinaturas:", [(a["usuario"], a["plano"], str(a["valor"]), a["status"])
                                for a in listar_assinaturas(ids["usuario"])])
        print("  Historico:", [(h["conteudo"], h["temporada"], h["progresso_minutos"])
                               for h in listar_historico(ids["usuario"])])
        ind = obter_indicadores()
        print("  Indicadores:", {k: v for k, v in ind.items() if k != "top_conteudos"})

        print("4) Validacoes e regras (todas devem dar erro)")
        esperar_erro("nome vazio", lambda: criar_usuario("", "x@x.com"))
        esperar_erro("e-mail invalido", lambda: criar_usuario("Bia", "email-invalido"))
        esperar_erro("e-mail duplicado", lambda: criar_usuario("Outro", f"teste_{s}@example.com"))
        esperar_erro("filme sem duracao", lambda: criar_conteudo("F", "filme", 2024))
        esperar_erro("segunda assinatura ativa",
                     lambda: criar_assinatura(ids["usuario"], plano["id_plano"], date.today()))
        esperar_erro("ativa com data de termino",
                     lambda: criar_assinatura(ids["usuario"], plano["id_plano"], date.today(),
                                              data_termino=date.today()))
        esperar_erro("serie sem episodio", lambda: registrar_reproducao(ids["usuario"], ids["serie"], 5))
        esperar_erro("filme com episodio",
                     lambda: registrar_reproducao(ids["usuario"], ids["filme"], 5, ids["episodio"]))
        esperar_erro("progresso maior que a duracao", lambda: registrar_reproducao(ids["usuario"], ids["filme"], 500))
        esperar_erro("plano com valor zero", lambda: criar_plano(f"p{s}", 0))
        esperar_erro("episodio em filme", lambda: criar_episodio(ids["filme"], "X", 1, 1, 10))
        esperar_erro("episodio duplicado", lambda: criar_episodio(ids["serie"], "Dup", 1, 1, 10))
        esperar_erro("excluir plano em uso", lambda: excluir_plano(plano["id_plano"]))

        print("5) Encerrar assinatura e criar outra")
        encerrar_assinatura(ids["assinatura"])
        criar_assinatura(ids["usuario"], plano["id_plano"], date.today())
        print("  [OK] encerrada e nova assinatura ativa criada")
    finally:
        print("6) Limpeza")
        for chave, fn in [("usuario", excluir_usuario), ("filme", excluir_conteudo),
                          ("serie", excluir_conteudo), ("genero", excluir_genero)]:
            if chave in ids:
                try:
                    fn(ids[chave])
                except Exception as e:
                    print(f"  aviso ao limpar {chave}: {e}")
        print("  dados de teste removidos")
    print("\nRESULTADO:", "TUDO CERTO" if not falhas else f"{len(falhas)} falha(s): {falhas}")


if __name__ == "__main__":
    try:
        main()
    except ErroAplicacao as e:
        print("Erro:", e)