"""Cliente HTTP compartilhado pelas páginas do painel."""
import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/triagem").rstrip("/")


def cabecalhos():
    token = os.getenv("MEDIFLOW_API_TOKEN", "")
    return {"Authorization": "Bearer " + token} if token else {}


def consultar(caminho, **kwargs):
    headers = {**kwargs.pop("headers", {}), **cabecalhos()}
    resposta = requests.get(f"{API_URL}/{caminho}", timeout=15, headers=headers, **kwargs)
    resposta.raise_for_status()
    return resposta.json()


def enviar(caminho, payload):
    resposta = requests.post(
        f"{API_URL}{('/' + caminho) if caminho else ''}", json=payload, timeout=90, headers=cabecalhos(),
    )
    resposta.raise_for_status()
    return resposta.json()


def obter_original(caminho):
    resposta = requests.get(f"{API_URL}/original", params={"caminho": caminho}, timeout=15, headers=cabecalhos())
    resposta.raise_for_status()
    return resposta
