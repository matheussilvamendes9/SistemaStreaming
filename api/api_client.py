
import requests

API_URL = "http://localhost:8000/api/v1"


def fazer_requisicao(metodo, endpoint, token=None, dados=None):
    """
    Realiza uma requisição HTTP para a API do StreamHub.
    """

    url = f"{API_URL}{endpoint}"

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resposta = requests.request(
            method=metodo,
            url=url,
            headers=headers,
            json=dados,
            timeout=10
        )

        resposta.raise_for_status()

        if resposta.status_code == 204:
            return None

        return resposta.json()

    except requests.exceptions.HTTPError:
        try:
            erro = resposta.json()
            mensagem = erro.get("detail", "Erro na requisição.")
        except ValueError:
            mensagem = "A API retornou uma resposta inválida."

        raise Exception(mensagem)

    except requests.exceptions.ConnectionError:
        raise Exception("Não foi possível conectar à API do StreamHub.")

    except requests.exceptions.Timeout:
        raise Exception("A API demorou muito para responder.")

    except requests.exceptions.RequestException:
        raise Exception("Ocorreu um erro na comunicação com a API.")
