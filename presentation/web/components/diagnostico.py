"""Feedback de configuração sem exposição de credenciais."""
import requests
import streamlit as st
from presentation.web.api_client import consultar


def carregar_diagnostico(conexoes=False):
    try:
        with st.spinner("Verificando conexões…" if conexoes else "Verificando configuração da API…"):
            resultado = consultar("diagnostico?conexoes=" + str(conexoes).lower())
        if not isinstance(resultado, dict) or not isinstance(resultado.get("itens"), list):
            raise ValueError("Resposta incompatível")
        st.session_state.diagnostico = resultado
    except requests.HTTPError as exc:
        codigo = exc.response.status_code if exc.response is not None else None
        orientacao = {
            404: "A API em execução ainda não possui o diagnóstico. Reinicie a API para carregar a atualização; no modo memória, os dados serão perdidos.",
            401: "Confira MEDIFLOW_API_TOKEN: a interface deve usar o mesmo valor configurado na API.",
            503: "Confira a configuração de autenticação da API e reinicie o serviço após corrigir o .env.",
        }.get(codigo, "Confira a API e tente novamente. A falha não comprova indisponibilidade dos outros recursos.")
        st.session_state.diagnostico = {"itens": [{"recurso": "API", "estado": "erro", "mensagem": "Diagnóstico da API indisponível.", "orientacao": orientacao}]}
    except (requests.RequestException, ValueError):
        st.session_state.diagnostico = {"itens": [{"recurso": "API", "estado": "erro", "mensagem": "Diagnóstico da API indisponível.", "orientacao": "Confira se a API está iniciada e atualizada, API_URL e o token de serviço. Tente novamente."}]}


def exibir_diagnostico():
    resultado = st.session_state.get("diagnostico", {})
    itens = resultado.get("itens", [])
    st.subheader("Diagnóstico de configuração", icon=":material/monitor_heart:")
    st.caption("Configuração preenchida não comprova conexão. Resultados refletem o instante da verificação.")
    if resultado.get("verificado_em"):
        st.caption("Verificação (UTC): " + resultado["verificado_em"])
    for item in itens:
        texto = f"**{item['recurso']}** — {item['mensagem']}"
        if item.get("orientacao"):
            texto += "\n\n" + item["orientacao"]
        {"erro": st.error, "aviso": st.warning, "ok": st.success}.get(item["estado"], st.info)(texto)
    st.caption("Não envia documentos, não executa inferência e não envia alertas. A consulta manual testa leitura do bucket, sem criar ou alterar objetos.")
    if st.button("Verificar conexões", icon=":material/network_check:"):
        carregar_diagnostico(conexoes=True)
        st.rerun()
