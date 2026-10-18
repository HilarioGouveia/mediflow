"""
Roteador de Apresentação: Endpoints de Verificação de Saúde (Health Checks)
Fornece monitoramento de integridade (Liveness) e prontidão (Readiness)
para orquestradores de contêiner e instâncias na OCI Compute.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, status, Response
from pydantic import BaseModel, Field

from config.settings import settings
from infrastructure.oci_client.storage_factory import get_storage_adapter

router = APIRouter(
    tags=["Monitoramento & Saúde"]
)


class HealthStatusDTO(BaseModel):
    status: str = Field(..., examples=["healthy", "degraded", "unhealthy"])
    timestamp: str
    servico: str = "MediFlow Core API"
    versao: str = "1.0.0"


class ReadinessStatusDTO(HealthStatusDTO):
    dependencias: Dict[str, Any] = Field(
        ...,
        examples=[{
            "oci_object_storage": {"status": "ok", "bucket": "mediflow-documentos-clinicos"},
            "llm_service": {"status": "ok", "provider": "Google Gemini"}
        }]
    )


@router.get(
    "/health",
    response_model=HealthStatusDTO,
    status_code=status.HTTP_200_OK,
    summary="Verificação básica de integridade (Liveness)",
    description="Retorna HTTP 200 se a aplicação FastAPI estiver ativa e aceitando requisições."
)
async def liveness_check() -> HealthStatusDTO:
    """
    Liveness probe: Verifica se o processo da aplicação está vivo.
    """
    return HealthStatusDTO(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        servico="MediFlow Core API",
        versao="1.0.0"
    )


@router.get(
    "/health/ready",
    response_model=ReadinessStatusDTO,
    status_code=status.HTTP_200_OK,
    summary="Verificação detalhada de prontidão (Readiness)",
    description="Valida a disponibilidade das configurações críticas: OCI Object Storage e credenciais da LLM."
)
async def readiness_check(response: Response) -> ReadinessStatusDTO:
    """
    Readiness probe: Verifica se a aplicação possui credenciais e configurações
    necessárias para processar triagens clínicas ponta a ponta.
    """
    dependencias = {}
    is_pronto = True

    # 1. Checagem de configuração da LLM
    if settings.APP_MODE == "presentation" and not settings.PRESENTATION_USE_LLM:
        dependencias["llm_service"] = {"status": "ok", "provedor": "Simulação de apresentação", "autenticado": "não se aplica"}
    elif settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 10:
        dependencias["llm_service"] = {
            "status": "ok",
            "provedor": "Google Gemini",
            "autenticado": "não verificado"
        }
    else:
        dependencias["llm_service"] = {
            "status": "warning",
            "provedor": "Google Gemini",
            "motivo": "Chave GEMINI_API_KEY ausente ou inválida no .env"
        }
        is_pronto = False

    # 2. Consulta real ao adaptador selecionado, sem inferência ou gravação.
    try:
        storage = get_storage_adapter()
        storage.listar_objetos_por_prefixo(settings.OCI_BUCKET_NAME, "_health/")
        dependencias["oci_object_storage"] = {
            "status": "ok",
            "bucket": settings.OCI_BUCKET_NAME,
            "namespace": getattr(storage, "namespace", None),
            "modo": storage.modo,
        }
    except Exception:
        dependencias["oci_object_storage"] = {
            "status": "error",
            "motivo": "Armazenamento configurado não está disponível.",
            "modo": settings.STORAGE_MODE,
        }
        is_pronto = False

    status_geral = "healthy" if is_pronto else "degraded"
    
    # Se uma dependência essencial falhar, responde HTTP 503 para balanceadores
    if not is_pronto:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessStatusDTO(
        status=status_geral,
        timestamp=datetime.now(timezone.utc).isoformat(),
        servico="MediFlow Core API",
        versao="1.0.0",
        dependencias=dependencias
    )
