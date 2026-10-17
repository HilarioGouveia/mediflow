"""
Interface Web MediFlow (Streamlit)
Painel Unificado de Triagem, Monitoramento de Emergências e Auditoria Human-in-the-Loop.
"""

import os
import base64
import requests
import streamlit as st

from presentation.web.components import (
    renderizar_visualizador_documento,
    renderizar_resumo_clinico
)
from presentation.web.views.fila_urgencias import renderizar_fila_urgencias
from presentation.web.views.auditoria import renderizar_painel_auditoria

API_URL = os.getenv("API_URL", "http://localhost:8000/triagem")

st.set_page_config(page_title="MediFlow - Triagem & Auditoria", layout="wide", page_icon="🏥")

st.title("🏥 MediFlow — Agente Autônomo de Triagem Clínica")
st.caption("Clean Architecture + Hexagonal integrada ao OCI Object Storage Always Free")

tabs = st.tabs([
    "📄 Nova Triagem", 
    "🚨 Fila de Emergência", 
    "⚠️ Auditoria Humana", 
    "📊 Indicadores"
])

# ABA 1: Ingestão de Documentos
with tabs[0]:
    st.subheader("Submeter Documento Clínico")
    col_input, col_view = st.columns([1, 1], gap="medium")

    with col_input:
        doc_id = st.text_input("ID do Documento", value="DOC-CLIN-2026-8942")
        canal_origem = st.selectbox("Canal de Origem", ["Pronto_Socorro", "Ambulatorio", "Recepcao"])
        tipo_arquivo = st.selectbox("Formato do Arquivo", ["TEXTO", "PDF", "IMAGEM"])

        texto_clinico = ""
        arquivo_base64 = None

        if tipo_arquivo == "TEXTO":
            texto_clinico = st.text_area(
                "Texto do Documento",
                height=220,
                placeholder="Insira o texto clínico para triagem..."
            )
        else:
            uploaded_file = st.file_uploader("Fazer Upload do Arquivo", type=["pdf", "png", "jpg", "jpeg"])
            if uploaded_file:
                bytes_data = uploaded_file.read()
                arquivo_base64 = base64.b64encode(bytes_data).decode("utf-8")

        enviar = st.button("Executar Triagem Automatizada", type="primary", use_container_width=True)

    with col_view:
        st.subheader("Diagnóstico & Roteamento")
        if enviar:
            payload = {
                "documento_id": doc_id,
                "tipo_arquivo": tipo_arquivo,
                "documento_texto": texto_clinico if tipo_arquivo == "TEXTO" else None,
                "arquivo_base64": arquivo_base64,
                "canal_origem": canal_origem
            }
            try:
                with st.spinner("Processando pelo grafo condicional de agentes..."):
                    resp = requests.post(API_URL, json=payload, timeout=60)

                if resp.status_code == 200:
                    dados = resp.json()
                    renderizar_resumo_clinico(
                        dados_extraidos=dados["dados_extraidos"],
                        classificacao=dados["classificacao"]
                    )
                    st.caption(f"☁️ Destino OCI: `{dados['armazenamento_oci']['caminho_objeto']}`")
                else:
                    st.error(f"Erro {resp.status_code}: {resp.text}")
            except Exception as exc:
                st.error(f"Falha ao conectar com o backend FastAPI: {exc}")

# ABA 2: Fila de Casos Urgentes
with tabs[1]:
    renderizar_fila_urgencias()

# ABA 3: Fila de Revisão Human-in-the-Loop
with tabs[2]:
    renderizar_painel_auditoria()

# ABA 4: Indicadores
with tabs[3]:
    m1, m2, m3 = st.columns(3)
    m1.metric("Triagens Realizadas", "1.240")
    m2.metric("Casos de Urgência Roteados", "182", delta="14.6%")
    m3.metric("Taxa de Autonomia sem Intervenção", "91.4%")