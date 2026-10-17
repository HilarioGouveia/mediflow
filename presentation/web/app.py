"""Painel operacional MediFlow."""
import base64
import json
from uuid import uuid4

import requests
import streamlit as st

from presentation.web.api_client import consultar, enviar
from presentation.web.components.clinical_card import renderizar_resumo_clinico
from presentation.web.components.pdf_viewer import renderizar_visualizador_documento
from presentation.web.views.auditoria import renderizar_painel_auditoria
from presentation.web.views.fila_urgencias import renderizar_fila_urgencias

st.set_page_config(page_title="MediFlow | Triagem clínica", page_icon=":material/health_and_safety:", layout="wide")
for chave, valor in {"resultado_triagem": None, "original_triagem": None, "novo_documento_id": f"DOC-{uuid4().hex[:12].upper()}"}.items():
    st.session_state.setdefault(chave, valor)

with st.sidebar:
    st.title(":material/health_and_safety: MediFlow")
    st.caption("Triagem documental clínica")
    pagina = st.radio("Navegação", ["Nova triagem", "Urgências", "Auditoria", "Histórico", "Integrações"], label_visibility="collapsed")
    st.divider()
    st.caption("IA, persistência e alertas têm estados independentes.")
    if st.button("Atualizar dados", icon=":material/refresh:", width="stretch"):
        st.rerun()

st.caption("MEDIFLOW / " + pagina.upper())
try:
    integracoes = consultar("integracoes")
except (requests.RequestException, ValueError):
    integracoes = None
if integracoes:
    modo = integracoes["armazenamento"]["modo"]
    if modo == "simulado":
        st.warning("Armazenamento em memória: os dados serão perdidos ao reiniciar a API. Não há comprovação de gravação na OCI.")
    elif modo == "emulador_oci":
        st.info("OCI emulado localmente: documentos preservados no volume Docker. Este ambiente não comprova persistência na Oracle Cloud.")
    else:
        st.caption("Adaptador OCI ativo · conexão e camada Always Free precisam de validação operacional.")
else:
    st.warning("Não foi possível consultar as integrações. Verifique se a API está disponível e atualizada.")


def exibir_resultado(doc):
    if doc.get("erro_extracao"):
        st.error("Extração não realizada: " + doc["erro_extracao"]["mensagem"])
        st.caption("A prioridade clínica não foi avaliada. Documento encaminhado para revisão humana.")
    else:
        renderizar_resumo_clinico(doc.get("dados_extraidos", {}), doc.get("classificacao", {}))
    decisao = doc.get("decisao_roteamento", {})
    st.subheader("Encaminhamento")
    st.write("**Destino:**", decisao.get("destino_principal", "Não informado"))
    mensagem = decisao.get("justificativa_roteamento") or "Sem justificativa informada."
    if decisao.get("requer_auditoria_humana"):
        st.warning(mensagem)
    elif doc.get("classificacao", {}).get("nivel_prioridade") == "Urgente":
        st.error(mensagem)
    else:
        st.info(mensagem)
    armazenamento = doc.get("armazenamento_oci", {})
    if armazenamento.get("status_backup") == "falha":
        st.error("Falha ao salvar o resultado da triagem.")
    st.caption(f"Objeto: {armazenamento.get('caminho_objeto', 'Não informado')}")
    if decisao.get("notificacao_gerada"):
        st.caption("Alerta gerado. A entrega externa não é comprovada por este registro.")
    with st.expander("Dados estruturados"):
        st.json(doc)
    st.download_button("Baixar resultado JSON", json.dumps(doc, ensure_ascii=False, indent=2), file_name="triagem.json", mime="application/json")


if pagina == "Nova triagem":
    st.title("Do documento ao destino certo.")
    st.caption("Envie, confira a extração e acompanhe o encaminhamento.")
    entrada, resultado = st.columns(2, gap="large")
    with entrada:
        st.subheader("Enviar documento")
        formato = st.segmented_control("Entrada", ["Arquivo", "Texto", "JSON"], default="Arquivo")
        with st.form("nova_triagem"):
            doc_id = st.text_input("ID do documento", key="novo_documento_id")
            canal = st.selectbox("Canal de origem", ["Pronto_Socorro", "Ambulatorio", "Recepcao"])
            arquivo = None
            texto = ""
            if formato == "Arquivo":
                arquivo = st.file_uploader("Documento clínico", type=["pdf", "jpg", "jpeg", "png", "txt", "json"])
            else:
                texto = st.text_area("Conteúdo JSON" if formato == "JSON" else "Texto clínico", height=220)
            processar = st.form_submit_button("Executar triagem", type="primary", icon=":material/scan:", width="stretch")
        if processar:
            if not doc_id.strip() or not (arquivo or texto.strip()):
                st.error("Informe o ID e o conteúdo do documento.")
            else:
                try:
                    bruto = arquivo.getvalue() if arquivo else texto.encode("utf-8")
                    nome = arquivo.name.lower() if arquivo else ""
                    tipo = "PDF" if nome.endswith(".pdf") else "IMAGEM" if nome.endswith((".jpg", ".jpeg", ".png")) else "JSON" if formato == "JSON" or nome.endswith(".json") else "TEXTO"
                    textual = bruto.decode("utf-8") if tipo in ("TEXTO", "JSON") else None
                    if tipo == "JSON":
                        json.loads(textual)
                    payload = {"documento_id": doc_id.strip(), "canal_origem": canal, "tipo_arquivo": tipo, "documento_texto": textual, "arquivo_base64": base64.b64encode(bruto).decode("ascii") if textual is None else None}
                    st.session_state.resultado_triagem = None
                    st.session_state.original_triagem = None
                    with st.spinner("Extraindo dados e avaliando o encaminhamento…"):
                        doc = enviar("", payload)
                    st.session_state.resultado_triagem = doc
                    st.session_state.original_triagem = (bruto, tipo)
                except (ValueError, UnicodeDecodeError):
                    st.error("Conteúdo inválido. Use texto UTF-8 ou um JSON válido.")
                except requests.RequestException:
                    st.error("Não foi possível concluir a triagem. Verifique a API antes de reenviar.")
        if st.session_state.original_triagem:
            with st.expander("Conferir documento enviado"):
                renderizar_visualizador_documento(*st.session_state.original_triagem)
    with resultado:
        st.subheader("Resultado da triagem")
        if st.session_state.resultado_triagem:
            exibir_resultado(st.session_state.resultado_triagem)
        else:
            st.info("O resultado mostrará os dados extraídos, a confiança e o motivo do encaminhamento.")
            st.caption("Recebimento → Extração → Decisão → Armazenamento")
elif pagina == "Urgências":
    renderizar_fila_urgencias()
elif pagina == "Auditoria":
    renderizar_painel_auditoria()
elif pagina == "Histórico":
    st.title("Histórico documental")
    st.caption("Estado atual dos documentos armazenados; não representa um log de eventos ou confirmação de atendimento.")
    try:
        documentos = consultar("historico")
    except (requests.RequestException, ValueError):
        st.error("Não foi possível consultar o histórico. Não há dados confirmados para exibir.")
        documentos = None
    if documentos is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Documentos armazenados", len(documentos))
        c2.metric("Classificados como urgentes", sum(d.get("classificacao", {}).get("nivel_prioridade") == "Urgente" for d in documentos))
        c3.metric("Aguardando revisão", sum(bool(d.get("decisao_roteamento", {}).get("requer_auditoria_humana")) for d in documentos))
        busca = st.text_input("Buscar por ID ou paciente")
        filtrados = [d for d in documentos if busca.casefold() in (d.get("documento_id", "") + " " + str((d.get("dados_extraidos", {}).get("paciente") or {}).get("nome") or "")).casefold()]
        if not filtrados:
            st.info("Nenhum documento encontrado.")
        else:
            indice = st.selectbox("Documento", range(len(filtrados)), format_func=lambda i: filtrados[i]["documento_id"])
            exibir_resultado(filtrados[indice])
else:
    st.title("Integrações")
    st.caption("Configuração disponível não comprova conexão nem entrega externa.")
    if integracoes:
        st.subheader("Modelo de IA")
        st.write("Provedor:", integracoes["ia"]["provedor"])
        st.write("Modelo:", integracoes["ia"].get("modelo", "Não informado"))
        st.write("Conexão:", integracoes["ia"]["conexao"])
        st.subheader("Armazenamento")
        st.write("Modo:", integracoes["armazenamento"]["modo"])
        st.write("Bucket:", integracoes["armazenamento"]["bucket"])
        st.subheader("Alertas")
        st.write("Modo:", integracoes["alertas"]["modo"])
        st.write("Entrega:", integracoes["alertas"]["entrega"])
