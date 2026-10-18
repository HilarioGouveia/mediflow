"""Fila de documentos classificados como urgentes."""
import requests
import streamlit as st
from presentation.web import api_client
from presentation.web.components.clinical_card import renderizar_resumo_clinico
from presentation.web.components.layout import cabecalho, indicadores, estado_vazio, nome_destino


def renderizar_fila_urgencias():
    cabecalho("Urgências", "Acompanhe os documentos classificados como urgentes e seus encaminhamentos.")
    try:
        casos = api_client.consultar("filas/urgencias")
    except (requests.RequestException, ValueError):
        st.error("Não foi possível consultar a fila de urgências. Tente atualizar os dados.")
        return
    indicadores([("Documentos urgentes", len(casos)), ("Exigem revisão", sum(bool(d.get("decisao_roteamento", {}).get("requer_auditoria_humana")) for d in casos))])
    st.caption("Classificação documental; esta lista não confirma atendimento clínico nem recebimento de alertas.")
    if not casos:
        estado_vazio("Nenhum documento urgente", "Os documentos classificados como urgentes aparecerão nesta fila.", ":material/emergency:")
        return
    with st.container(border=True):
        st.subheader("Pesquisar na fila", icon=":material/search:")
        esquerda, direita = st.columns(2)
        with esquerda:
            busca = st.text_input("Buscar documento ou paciente", placeholder="ID ou nome do paciente")
        with direita:
            revisao = st.selectbox("Revisão humana", ["Todos", "Exige revisão", "Sem revisão pendente"])
    encontrados = 0
    for caso in casos:
        paciente = (caso.get("dados_extraidos", {}).get("paciente") or {}).get("nome") or "Não identificado"
        decisao = caso.get("decisao_roteamento", {})
        exige_revisao = bool(decisao.get("requer_auditoria_humana"))
        if busca.casefold() not in (caso["documento_id"] + " " + paciente).casefold():
            continue
        if revisao == "Exige revisão" and not exige_revisao or revisao == "Sem revisão pendente" and exige_revisao:
            continue
        encontrados += 1
        with st.container(border=True):
            st.badge("Urgente", color="red", icon=":material/emergency:")
            st.subheader(paciente)
            st.caption(caso["documento_id"] + " · " + (caso.get("classificacao", {}).get("tipo_documento") or "Documento clínico"))
            st.error(decisao.get("justificativa_roteamento") or "Documento classificado como urgente.")
            st.write("**Destino:**", nome_destino(decisao.get("destino_principal")))
            st.caption("Alerta gerado; entrega externa não comprovada." if decisao.get("notificacao_gerada") else "Sem alerta registrado.")
            if exige_revisao:
                st.badge("Revisão humana necessária", color="orange")
                st.page_link("app_pages/auditoria.py", label="Abrir revisão humana", icon=":material/fact_check:")
            with st.expander("Conferir dados extraídos", icon=":material/visibility:"):
                if caso.get("erro_extracao"):
                    st.error("Extração não realizada: " + caso["erro_extracao"]["mensagem"])
                else:
                    renderizar_resumo_clinico(caso.get("dados_extraidos", {}), caso.get("classificacao", {}))
            with st.expander("Dados estruturados", icon=":material/data_object:"):
                st.json(caso)
    if not encontrados:
        estado_vazio("Nenhum documento encontrado", "Ajuste os filtros para consultar a fila.", ":material/search_off:")
