"""Fila de documentos classificados como urgentes."""
import requests
import streamlit as st

from presentation.web.api_client import consultar
from presentation.web.components.clinical_card import renderizar_resumo_clinico


def renderizar_fila_urgencias():
    st.title("Urgências")
    st.caption("Documentos classificados como urgentes. Esta lista não confirma atendimento clínico.")
    try:
        casos = consultar("filas/urgencias")
    except (requests.RequestException, ValueError):
        st.error("Não foi possível consultar a fila de urgências. Tente atualizar os dados.")
        return
    st.metric("Documentos na fila", len(casos))
    if not casos:
        st.info("Nenhum documento urgente encontrado na consulta.")
    for caso in casos:
        with st.container(border=True):
            st.caption(caso["documento_id"])
            renderizar_resumo_clinico(caso.get("dados_extraidos", {}), caso.get("classificacao", {}))
            decisao = caso.get("decisao_roteamento", {})
            st.error(decisao.get("justificativa_roteamento") or "Achado crítico identificado.")
            st.write("**Destino:**", decisao.get("destino_principal", "Não informado"))
            st.caption("Alerta gerado; entrega externa não comprovada." if decisao.get("notificacao_gerada") else "Sem alerta registrado.")
            with st.expander("Dados estruturados"):
                st.json(caso)
