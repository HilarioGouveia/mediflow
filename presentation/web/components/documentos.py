"""Apresentação dos estados reais dos documentos armazenados."""
from presentation.web.components.layout import nome_destino


def estado_documento(doc):
    if doc.get("erro_extracao"):
        return "Falha na extração"
    if doc.get("decisao_roteamento", {}).get("requer_auditoria_humana"):
        return "Aguardando revisão"
    return {"processado": "Processado", "erro": "Erro", "em_analise": "Em análise"}.get(doc.get("status"), "Não informado")


def linhas_documentos(documentos):
    return [{
        "Documento": d.get("documento_id", "Não informado"),
        "Paciente": (d.get("dados_extraidos", {}).get("paciente") or {}).get("nome") or "Não identificado",
        "Tipo": d.get("classificacao", {}).get("tipo_documento") or "Não identificado",
        "Prioridade": "Não avaliada" if d.get("erro_extracao") else d.get("classificacao", {}).get("nivel_prioridade", "Não informada"),
        "Estado": estado_documento(d),
        "Destino": nome_destino(d.get("decisao_roteamento", {}).get("destino_principal")),
    } for d in documentos]
