"""Consultas do painel. Não realizam chamadas de inferência ou envio de alertas."""
from fastapi import APIRouter, Depends, HTTPException, Response

from infrastructure.oci_client.client_factory import get_triagem_use_case
from config.settings import settings

router = APIRouter(prefix="/triagem", tags=["Painel"])


@router.get("/integracoes")
def consultar_integracoes(use_case=Depends(get_triagem_use_case)):
    return {
        "armazenamento": {
            "modo": use_case.storage.modo,
            "bucket": use_case.bucket_name,
            "conexao": "não verificada",
            "namespace": getattr(use_case.storage, "namespace", None),
        },
        "ia": {"provedor": "Google Gemini", "modelo": settings.GEMINI_MODEL_NAME, "conexao": "não verificada"},
        "alertas": {
            "modo": "webhook" if use_case.notifier.webhook_url else "somente_log",
            "entrega": "não verificada",
        },
    }


@router.get("/historico")
def listar_historico(use_case=Depends(get_triagem_use_case)):
    documentos = []
    for prefixo in ("processados/", "auditoria_humana/"):
        for chave in use_case.storage.listar_objetos_por_prefixo(use_case.bucket_name, prefixo):
            if chave.endswith(".json"):
                doc = use_case.storage.obter_json(use_case.bucket_name, chave)
                if doc:
                    documentos.append(doc)
    return documentos


@router.get("/original")
def obter_original(caminho: str, use_case=Depends(get_triagem_use_case)):
    if not caminho.startswith("recebidos/") or ".." in caminho.split("/"):
        raise HTTPException(422, "Caminho de documento original inválido.")
    conteudo = use_case.storage.obter_arquivo(use_case.bucket_name, caminho)
    if conteudo is None:
        raise HTTPException(404, "Documento original não disponível.")
    tipo = "application/octet-stream"
    if conteudo.startswith(b"%PDF"):
        tipo = "application/pdf"
    elif conteudo.startswith(b"\x89PNG"):
        tipo = "image/png"
    elif conteudo.startswith(b"\xff\xd8"):
        tipo = "image/jpeg"
    elif caminho.endswith((".txt", ".json")):
        tipo = "text/plain; charset=utf-8"
    return Response(conteudo, media_type=tipo, headers={"Cache-Control": "no-store"})
