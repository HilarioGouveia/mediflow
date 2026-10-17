"""Cliente HTTP compartilhado pelas páginas do painel."""
import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/triagem").rstrip("/")


def consultar(caminho, **kwargs):
    resposta = requests.get(f"{API_URL}/{caminho}", timeout=15, **kwargs)
    resposta.raise_for_status()
    return resposta.json()


def enviar(caminho, payload):
    resposta = requests.post(
        f"{API_URL}{('/' + caminho) if caminho else ''}", json=payload, timeout=90,
    )
    resposta.raise_for_status()
    return resposta.json()
