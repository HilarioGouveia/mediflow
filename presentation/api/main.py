"""
Ponto de entrada da API REST MediFlow.
Registra os roteadores modulares e inicializa a aplicação FastAPI.
"""

from fastapi import FastAPI
from presentation.api.routers.health_router import router as health_router
from presentation.api.routers.triagem_router import router as triagem_router
from presentation.api.routers.painel_router import router as painel_router
from presentation.api.auth import proteger_api

app = FastAPI(
    title="MediFlow API",
    description="Agente autônomo para triagem, extração multimodal e roteamento clínico.",
    version="1.0.0"
)

# Inclusão dos roteadores modulares
app.middleware("http")(proteger_api)
app.include_router(health_router)
app.include_router(triagem_router)
app.include_router(painel_router)
