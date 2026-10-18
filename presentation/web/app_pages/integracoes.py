"""Estado dos adaptadores e organização lógica do armazenamento."""
import streamlit as st
from pathlib import Path
import os
import requests
from presentation.web.api_client import consultar
from presentation.web.components.layout import cabecalho
from presentation.web.components.diagnostico import exibir_diagnostico

integracoes = st.session_state.get("integracoes")
cabecalho("Armazenamento e integrações", "Consulte o ambiente de armazenamento, o modelo de IA e o canal de alertas.", "Plataforma")
exibir_diagnostico()
with st.container(border=True):
    st.subheader("Execução da interface", icon=":material/computer:")
    ambiente = {"local": "Local", "cloud": "Cloud"}.get(os.getenv("APP_ENV", "local").strip().lower(), "Não reconhecido")
    st.write("**Ambiente:**", ambiente)
    st.write("**Execução:**", "Docker" if Path("/.dockerenv").exists() else "Python direto")
    st.caption("Informações do servidor Streamlit. A API e o armazenamento podem executar em outros ambientes.")
if not integracoes:
    st.error("Não foi possível consultar as integrações. Verifique a disponibilidade da API.")
    st.stop()

armazenamento = integracoes["armazenamento"]
modo = armazenamento["modo"]
nomes = {"simulado": "Memória temporária", "emulador_oci": "OCI local em Docker", "oci": "Oracle Cloud Infrastructure"}
with st.container(border=True):
    st.subheader(nomes.get(modo, modo), icon=":material/cloud:")
    st.badge("Adaptador configurado", color="gray", icon=":material/settings:")
    if modo == "emulador_oci":
        st.caption("Os documentos ficam no armazenamento do emulador OCI; no Compose fornecido, são preservados em um volume Docker.")
    elif modo == "simulado":
        st.warning("Armazenamento temporário: os dados são perdidos ao reiniciar a API.")
    else:
        st.caption("Adaptador da Oracle Cloud selecionado. A conexão precisa de validação operacional.")
    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Bucket**")
        st.write(armazenamento["bucket"])
    with direita:
        st.markdown("**Namespace**")
        st.write(armazenamento.get("namespace") or "Não se aplica / não informado")
    st.caption("Teste de conexão: " + armazenamento.get("conexao", "não verificada"))

st.subheader("Organização documental", icon=":material/folder_open:")
try:
    inventario = consultar("armazenamento/objetos")
    if not isinstance(inventario, dict) or not isinstance(inventario.get("objetos"), list) or not isinstance(inventario.get("contagens"), dict):
        raise ValueError("Resposta inválida")
except (requests.RequestException, ValueError):
    inventario = None
    st.warning("Não foi possível listar os objetos armazenados. Confira a API atualizada, a conexão e as permissões. Use Atualizar dados para tentar novamente.")
st.caption("Contagens de objetos por prefixo no bucket configurado; originais e resultados são objetos distintos. Falhas de processamento são estados nas filas, não uma pasta separada.")
with st.container(horizontal=True):
    for titulo, descricao, prefixo, icone in [
        ("Documentos recebidos", "Originais enviados para triagem.", "recebidos/", ":material/inbox:"),
        ("Documentos processados", "Resultados organizados por prioridade.", "processados/", ":material/task_alt:"),
        ("Revisão humana", "Triagens que exigem conferência.", "auditoria_humana/", ":material/fact_check:"),
        ("Acompanhamento interno", "Registros de etapas e rastreabilidade.", "fluxo/", ":material/history:"),
    ]:
        with st.container(border=True, width=260):
            st.markdown(f"{icone} **{titulo}**")
            st.caption(descricao)
            st.code(prefixo, language=None)
            st.caption(f"{inventario['contagens'].get(prefixo, 0)} objeto(s)" if inventario is not None else "Contagem indisponível")

st.subheader("Objetos armazenados", icon=":material/storage:")
if inventario is not None:
    if not inventario["objetos"]:
        st.info("Nenhum objeto encontrado nas áreas consultadas.")
    else:
        areas = ["Todas"] + sorted({o["area"] for o in inventario["objetos"]})
        area = st.selectbox("Área do armazenamento", areas)
        busca = st.text_input("Buscar nome ou caminho do objeto", placeholder="Ex.: recebidos/ ou DOC-")
        linhas = [{"Área": o["area"], "Nome do objeto": o["nome"], "Tipo": o["tipo"], "Localização lógica": o["caminho"], "Estado": o["estado"]} for o in inventario["objetos"] if (area == "Todas" or area == o["area"]) and busca.casefold() in o["caminho"].casefold()]
        if linhas:
            st.dataframe(linhas, hide_index=True, alt="Objetos listados no armazenamento por área, nome, tipo e localização lógica")
        else:
            st.info("Nenhum objeto corresponde aos filtros.")
    st.caption("Listado confirma presença na consulta; não comprova integridade ou backup externo. Nome é a chave do objeto, não necessariamente o nome original enviado. Data e tamanho não são informados por esta consulta.")
    st.page_link("app_pages/documentos.py", label="Consultar resultados dos documentos", icon=":material/description:")

ia, alertas = st.columns(2)
with ia.container(border=True):
    st.subheader("Inteligência artificial", icon=":material/auto_awesome:")
    st.write("**Provedor:**", integracoes["ia"]["provedor"])
    st.write("**Modelo:**", integracoes["ia"].get("modelo", "Não informado"))
    st.caption("Conexão: " + integracoes["ia"]["conexao"])
with alertas.container(border=True):
    st.subheader("Alertas", icon=":material/notifications:")
    modo_alertas = integracoes["alertas"]["modo"]
    st.write("**Canal:**", {"somente_log": "Registro em log", "webhook": "Webhook"}.get(modo_alertas, modo_alertas))
    st.caption("Entrega: " + integracoes["alertas"]["entrega"])

st.caption("Esta página consulta a configuração e permite verificar a leitura do bucket. Não executa inferência, gravação de teste ou envio de alertas.")
