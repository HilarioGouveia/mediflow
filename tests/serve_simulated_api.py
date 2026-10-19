"""Entrada exclusiva do Compose de testes; nunca chama Gemini ou webhooks."""
import uvicorn

from infrastructure.adapters.presentation_llm_adapter import PresentationLLMAdapter
from infrastructure.oci_client import client_factory


if __name__ == "__main__":
    if client_factory.settings.STORAGE_MODE != "emulator":
        raise RuntimeError("A API de testes exige STORAGE_MODE=emulator")
    client_factory.GeminiLLMAdapter = lambda **kwargs: PresentationLLMAdapter()
    client_factory.settings.WEBHOOK_URL = ""
    client_factory.get_triagem_use_case.cache_clear()
    uvicorn.run("presentation.api.main:app", host="0.0.0.0", port=8000)
