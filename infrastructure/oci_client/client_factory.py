"""
Fábrica de Injeção de Dependências (Client Factory)
"""

from functools import lru_cache
import logging
import os
import oci

from config.settings import settings
from application.use_cases.processar_triagem import ProcessarTriagemUseCase
from infrastructure.adapters.gemini_llm_adapter import GeminiLLMAdapter
from infrastructure.adapters.oci_storage_adapter import OCIStorageAdapter
from infrastructure.adapters.webhook_notifier import WebhookNotifierAdapter

logger = logging.getLogger("MediFlowFactory")


@lru_cache()
def get_triagem_use_case() -> ProcessarTriagemUseCase:
    """
    Constrói a instância singleton do ProcessarTriagemUseCase.
    Garante inicialização resiliente mesmo se ~/.oci/config não existir localmente.
    """
    oci_config = {}
    config_path = os.path.expanduser(settings.OCI_CONFIG_FILE)

    if os.path.exists(config_path):
        try:
            oci_config = oci.config.from_file(
                file_location=config_path,
                profile_name=settings.OCI_CONFIG_PROFILE,
            )
        except Exception as exc:
            logger.warning("Erro ao ler credenciais OCI em %s: %s. Operando em modo de contingência.", config_path, exc)
    else:
        logger.info("Arquivo de configuração OCI (%s) não encontrado. Modo de contingência ativado.", config_path)

    llm_adapter = GeminiLLMAdapter(api_key=settings.GEMINI_API_KEY)
    storage_adapter = OCIStorageAdapter(config_dict=oci_config, namespace_name=settings.OCI_NAMESPACE)
    notifier_adapter = WebhookNotifierAdapter(webhook_url=getattr(settings, "WEBHOOK_URL", ""))

    return ProcessarTriagemUseCase(
        llm=llm_adapter,
        storage=storage_adapter,
        notifier=notifier_adapter,
        bucket_name=settings.OCI_BUCKET_NAME,
    )