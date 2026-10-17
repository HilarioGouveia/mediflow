"""Conferência lado a lado e homologação de pendências."""
import requests
import streamlit as st

from presentation.web.api_client import API_URL, consultar, enviar
from presentation.web.components.pdf_viewer import renderizar_visualizador_documento

DESTINOS = {
    "Prontuario_Eletronico_Paciente": "Prontuário eletrônico",
    "Farmacia_Hospitalar": "Farmácia hospitalar",
    "Auditoria_de_Autorizacoes": "Auditoria de autorizações",
    "Fila_Emergencia_Medica": "Emergência médica",
}


def renderizar_painel_auditoria():
    st.title("Conferir antes de encaminhar.")
    st.caption("Compare o documento original com a extração e registre sua decisão.")
    if "aviso_auditoria" in st.session_state:
        st.success(st.session_state.pop("aviso_auditoria"))
    try:
        fila = consultar("filas/auditoria")
    except (requests.RequestException, ValueError):
        st.error("Não foi possível consultar as pendências. Tente atualizar os dados.")
        return
    c1, c2 = st.columns(2)
    c1.metric("Documentos pendentes", len(fila))
    c2.metric("Limiar de confiança", "85%")
    if not fila:
        st.info("Nenhum documento pendente encontrado na consulta.")
        return
    indice = st.selectbox("Documento para revisão", range(len(fila)), format_func=lambda i: fila[i]["documento_id"])
    doc = fila[indice]
    dados = doc.get("dados_extraidos", {})
    origem = doc.get("armazenamento_oci", {}).get("caminho_objeto")
    esquerda, direita = st.columns(2, gap="large")
    with esquerda:
        st.subheader("Documento e motivo da retenção")
        st.warning(doc.get("decisao_roteamento", {}).get("justificativa_roteamento") or "Revisão necessária.")
        score = doc.get("classificacao", {}).get("score_confianca_classificacao", 0)
        if doc.get("erro_extracao"):
            st.error("Extração não realizada: " + doc["erro_extracao"]["mensagem"])
        else:
            st.write(f"Confiança da extração: {score:.1%}")
        bruto = doc.get("armazenamento_oci", {}).get("caminho_documento_bruto")
        if bruto:
            try:
                resp = requests.get(f"{API_URL}/original", params={"caminho": bruto}, timeout=15)
                resp.raise_for_status()
                mime = resp.headers.get("content-type", "")
                tipo = "PDF" if "pdf" in mime else "IMAGEM" if "image/" in mime else "TEXTO"
                renderizar_visualizador_documento(resp.content, tipo)
            except requests.RequestException:
                st.warning("Não foi possível carregar o original. Confira o documento antes de aprovar.")
        else:
            st.info("Este registro não possui referência ao original.")
        with st.expander("Extração completa"):
            st.json(doc)
    with direita:
        st.subheader("Revisar dados")
        with st.form(f"auditoria_{doc['documento_id']}"):
            paciente = st.text_input("Nome do paciente", value=(dados.get("paciente") or {}).get("nome") or "")
            crm = st.text_input("CRM / UF", value=(dados.get("medico_solicitante") or {}).get("crm") or "", placeholder="123456-SP")
            diagnostico = st.text_input("Diagnóstico principal", value=dados.get("diagnostico_principal") or "")
            cid = st.text_input("CID-10", value=dados.get("cid_sugerido") or "")
            destino = st.selectbox("Destino após aprovação", list(DESTINOS), format_func=DESTINOS.get)
            parecer = st.text_area("Parecer do auditor", placeholder="Descreva a conferência e as correções.")
            aprovar = st.form_submit_button("Aprovar e encaminhar", type="primary", width="stretch")
            rejeitar = st.form_submit_button("Rejeitar documento", width="stretch")
        if aprovar or rejeitar:
            if not parecer.strip() or (aprovar and (not paciente.strip() or not crm.strip())):
                st.error("Registre o parecer. Para aprovar, informe também o paciente e o CRM.")
                return
            if not origem:
                st.error("Registro sem caminho de origem. Não é possível homologar.")
                return
            payload = dict(documento_id=doc["documento_id"], origem_oci_path=origem, paciente_nome=paciente, crm_retificado=crm, diagnostico=diagnostico, cid_homologado=cid, destino_aprovado=destino, parecer_auditor=parecer.strip(), decisao="aprovar" if aprovar else "rejeitar")
            try:
                with st.spinner("Salvando a decisão…"):
                    resposta = enviar("homologar", payload)
            except (requests.RequestException, ValueError):
                st.error("Não foi possível confirmar a decisão. Atualize a fila antes de tentar novamente.")
                return
            mensagem = f"Decisão salva em {resposta['caminho_novo_oci']}."
            if resposta.get("notificacao_enviada") is False:
                mensagem += " O envio do alerta falhou."
            elif resposta.get("notificacao_enviada"):
                mensagem += " Notificador executado; consulte Integrações para verificar o modo de envio."
            st.session_state.aviso_auditoria = mensagem
            st.rerun()
