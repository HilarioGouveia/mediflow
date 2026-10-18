"""Credencial de serviço entre a UI autenticada e a API interna."""
from secrets import compare_digest
from fastapi import Request
from fastapi.responses import JSONResponse
from config.settings import settings


async def proteger_api(request: Request, call_next):
    if not settings.AUTH_ENABLED or (request.url.path == "/health" and request.method == "GET"):
        return await call_next(request)
    token = settings.MEDIFLOW_API_TOKEN.get_secret_value()
    if len(token) < 32:
        return JSONResponse({"detail": "Autenticação da API não configurada."}, status_code=503)
    recebido = request.headers.get("authorization", "")
    if not compare_digest(recebido.encode(), ("Bearer " + token).encode()):
        return JSONResponse({"detail": "Credencial de serviço ausente ou inválida."}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
    return await call_next(request)
