"""
Visão de Apresentação: Painel de Auditoria Clínica (Human-in-the-Loop)
Consulta pendências reais em /auditoria_humana/ no OCI e persiste a homologação humana na nuvem.
"""

import os
import requests
import streamlit as st

BASE_API = os.getenv("API_URL", "http://localhost:8000/triagem").replace("/triagem", "")


def renderizar_painel_auditoria():
    st.header("🔍 Painel de Auditoria Clínica — Human-in-the-Loop")
    st.markdown(
        "Fila de contingência integrada diretamente ao OCI Object Storage. "
        "Aprovações e correções movem o registro de `/auditoria_humana/` para `/processados/rotina/`."
    )

    try:
        resp = requests.get(f"{BASE_API}/triagem/filas/auditoria", timeout=10)
        fila_pendente = resp.json() if resp.status_code == 200 else []
    except Exception as exc:
        st.error(f"Erro ao conectar com OCI Object Storage: {exc}")
        fila_pendente = []

    col1, col2, col3 = st.columns(3)
    col1.metric("Pendentes no Bucket OCI", f"{len(fila_pendente)} docs")
#    col2.metric("Limiar Mínimo", "85.0%")
    col2.metric(
        "Limiar Mínimo Autônomo", 
        "85.0%", 
        help="Documentos com score abaixo de 0.85 são retidos obrigatoriamente."
)

    col3.metric("Armazenamento", "OCI Always Free")

    st.divider()

    if not fila_pendente:
        st.success("🎉 Não há documentos pendentes de auditoria no OCI Object Storage!")
        return

    opcoes_docs = {
        f"{d['documento_id']} - {d.get('dados_extraidos', {}).get('paciente', {}).get('nome', 'Sem Nome')}": d['documento_id']
        for d in fila_pendente
    }
    doc_selecionado_label = st.selectbox("Selecione o Documento para Homologação:", list(opcoes_docs.keys()))
    doc_id_alvo = opcoes_docs[doc_selecionado_label]

    doc = next(d for d in fila_pendente if d["documento_id"] == doc_id_alvo)
    caminho_oci_origem = doc.get("armazenamento_oci", {}).get("caminho_objeto")

    col_analise, col_edicao = st.columns([1, 1], gap="large")

    with col_analise:
        st.subheader("📑 Diagnóstico do Agente")
        justificativa = doc.get("decisao_roteamento", {}).get("justificativa_roteamento", "")
        st.warning(f"⚠️ **Motivo da Retenção:** {justificativa}")
        st.write(f"**Identificador:** `{doc.get('documento_id')}`")
        st.write(f"**Score IA:** `{doc.get('classificacao', {}).get('score_confianca_classificacao', 0.0) * 100:.1f}%`")
        st.write(f"**Objeto no OCI:** `{caminho_oci_origem}`")

        with st.expander("Exibir Dados Brutos do OCI (JSON)", expanded=True):
            st.json(doc)

    with col_edicao:
        st.subheader("✏️ Retificação & Homologação no OCI")
        paciente_dados = doc.get("dados_extraidos", {}).get("paciente", {})
        medico_dados = doc.get("dados_extraidos", {}).get("medico_solicitante", {})

        with st.form(key=f"form_auditoria_{doc['documento_id']}"):
            paciente_retificado = st.text_input("Nome do Paciente", value=paciente_dados.get("nome") or "")
            col_med1, col_med2 = st.columns(2)
            medico_retificado = col_med1.text_input("Médico Responsável", value=medico_dados.get("nome") or "")
            crm_retificado = col_med2.text_input("CRM com UF", value=medico_dados.get("crm") or "", placeholder="Ex: 145892-SP")

            diagnostico_retificado = st.text_input("Diagnóstico Principal", value=doc.get("dados_extraidos", {}).get("diagnostico_principal") or "")
            cid_retificado = st.text_input("CID-10 Homologado", value=doc.get("dados_extraidos", {}).get("cid_sugerido") or "")

            destino_aprovacao = st.selectbox(
                "Destino do Roteamento Pós-Auditoria",
                ["Prontuario_Eletronico_Paciente", "Farmacia_Hospitalar", "Auditoria_de_Autorizacoes", "Fila_Emergencia_Medica"]
            )
            parecer = st.text_area("Parecer do Auditor Humano", value="Dados conferidos e homologados manualmente.")

            b_col1, b_col2 = st.columns(2)
            aprovar = b_col1.form_submit_button("✅ Aprovar e Salvar no OCI", type="primary", use_container_width=True)
            rejeitar = b_col2.form_submit_button("❌ Rejeitar e Mover no OCI", use_container_width=True)

            if aprovar or rejeitar:
                acao = "aprovar" if aprovar else "rejeitar"
                payload_homologacao = {
                    "documento_id": doc["documento_id"],
                    "origem_oci_path": caminho_oci_origem,
                    "paciente_nome": paciente_retificado,
                    "crm_retificado": crm_retificado,
                    "diagnostico": diagnostico_retificado,
                    "cid_homologado": cid_retificado,
                    "destino_aprovado": destino_aprovacao,
                    "parecer_auditor": parecer,
                    "decisao": acao
                }
                with st.spinner("Atualizando registros no OCI Object Storage..."):
                    resp_homolog = requests.post(f"{BASE_API}/triagem/homologar", json=payload_homologacao, timeout=15)

                if resp_homolog.status_code == 200:
                    st.success(f"Homologação concluída com sucesso! Registro persistido no OCI: `{resp_homolog.json().get('caminho_novo_oci')}`")
                    st.rerun()
                else:
                    st.error(f"Erro ao persistir no OCI: {resp_homolog.text}")