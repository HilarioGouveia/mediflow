"""Visão operacional baseada exclusivamente nos registros persistidos."""
import requests
import streamlit as st
from presentation.web.api_client import consultar
from presentation.web.components.documentos import linhas_documentos
from presentation.web.components.layout import cabecalho

cabecalho("Central de triagem", "Documentos, prioridades e revisões em um só lugar.")
with st.container(horizontal=True):
    st.page_link("app_pages/nova_triagem.py", label="Nova triagem", icon=":material/add_circle:")
    st.page_link("app_pages/documentos.py", label="Consultar documentos", icon=":material/description:")

try:
    documentos = consultar("historico")
except (requests.RequestException, ValueError):
    st.error("Não foi possível carregar os documentos. Confira a API e tente atualizar os dados.")
    st.stop()

revisoes = sum(bool(d.get("decisao_roteamento", {}).get("requer_auditoria_humana")) for d in documentos)
urgentes = sum(not d.get("erro_extracao") and d.get("classificacao", {}).get("nivel_prioridade") == "Urgente" for d in documentos)
falhas = sum(bool(d.get("erro_extracao")) for d in documentos)
for coluna, (rotulo, valor) in zip(st.columns(4), [("Documentos armazenados", len(documentos)), ("Aguardando revisão", revisoes), ("Classificados urgentes", urgentes), ("Falhas de extração", falhas)]):
    coluna.metric(rotulo, valor, border=True, height="stretch")
st.caption("Contagens do estado atual dos registros. Urgências podem também exigir revisão; não indicam atendimento pendente.")

if not documentos:
    with st.container(border=True):
        st.subheader("Tudo pronto para a primeira triagem", icon=":material/upload_file:")
        st.write("Envie um documento para começar a organizar o fluxo. Os registros salvos aparecerão aqui.")
        st.page_link("app_pages/nova_triagem.py", label="Enviar primeiro documento", icon=":material/arrow_forward:")
else:
    with st.container(border=True):
        st.subheader("Documentos clínicos", icon=":material/description:")
        busca = st.text_input("Buscar documento ou paciente", placeholder="Digite o ID ou nome do paciente")
        linhas = linhas_documentos(documentos)
        linhas = [linha for linha in linhas if busca.casefold() in (linha["Documento"] + " " + linha["Paciente"]).casefold()]
        if linhas:
            st.dataframe(linhas, hide_index=True, alt="Documentos armazenados com prioridade, estado e destino")
        else:
            st.info("Nenhum documento corresponde à busca.")
    with st.container(border=True):
        st.subheader("Atenção e acompanhamento", icon=":material/fact_check:")
        st.write(f"{revisoes} documento(s) exigem revisão humana. {falhas} registro(s) apresentam falha de extração.")
        st.page_link("app_pages/auditoria.py", label="Abrir revisão humana", icon=":material/arrow_forward:")

with st.expander("Como funciona o fluxo", icon=":material/route:"):
    st.write("Recebimento → Extração e validação → Encaminhamento → Revisão humana, quando necessária.")
    st.caption("O resultado apresenta a justificativa do encaminhamento. A confirmação de armazenamento e os alertas são informados separadamente.")
