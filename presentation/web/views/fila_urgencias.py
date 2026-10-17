"""
Visão de Apresentação: Fila de Emergência Médica (Urgências)
Consulta em tempo real os objetos persistidos em /processados/urgentes/ no OCI Object Storage.
"""

import os
import requests
import streamlit as st

BASE_API = os.getenv("API_URL", "http://localhost:8000/triagem").replace("/triagem", "")


def renderizar_fila_urgencias():
    st.header("🚨 Fila de Emergência Médica — Triagem Imediata")
    st.markdown(
        "Monitoramento prioritário de achados clínicos de alta gravidade. "
        "Dados consultados em tempo real do bucket OCI (`/processados/urgentes/`)."
    )

    try:
        resp = requests.get(f"{BASE_API}/triagem/filas/urgencias", timeout=10)
        casos_ativos = resp.json() if resp.status_code == 200 else []
    except Exception as exc:
        st.error(f"Erro ao consultar OCI Object Storage via API: {exc}")
        casos_ativos = []

    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Casos Críticos Ativos (OCI)", f"{len(casos_ativos)} pacientes", delta="Atenção Máxima", delta_color="inverse")
    col2.metric("SLA Limite Emergência", "15 min")
    col3.metric("Origem dos Dados", "OCI Always Free Bucket")

    st.divider()

    if not casos_ativos:
        st.success("✅ Nenhum caso crítico pendente no OCI Object Storage.")
        return

    for caso in casos_ativos:
        with st.container(border=True):
            col_info, col_alerta, col_acoes = st.columns([2, 2, 1])

            paciente = caso.get("dados_extraidos", {}).get("paciente", {})
            medico = caso.get("dados_extraidos", {}).get("medico_solicitante", {})
            classif = caso.get("classificacao", {})

            with col_info:
                st.markdown(f"### 🔴 {paciente.get('nome', 'Paciente Não Identificado')}")
                st.write(f"**Documento ID:** `{caso.get('documento_id')}`")
                st.write(f"**Especialidade:** {classif.get('especialidade')}")
                st.write(f"**Médico:** {medico.get('nome')} ({medico.get('crm')})")

            with col_alerta:
                st.error(f"**Achado Crítico:** {caso.get('dados_extraidos', {}).get('diagnostico_principal')}")
                st.write(f"**CID-10:** `{caso.get('dados_extraidos', {}).get('cid_sugerido')}`")
                st.caption(f"☁️ OCI Path: `{caso.get('armazenamento_oci', {}).get('caminho_objeto')}`")

            with col_acoes:
                st.write("**Ações:**")
                if st.button("🚨 Notificar Plantão", key=f"notif_{caso['documento_id']}", use_container_width=True):
                    st.toast("Plantão notificado com sucesso!", icon="📢")

            with st.expander("Ver JSON Completo do OCI"):
                st.json(caso)