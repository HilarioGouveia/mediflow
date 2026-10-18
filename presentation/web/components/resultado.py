"""Apresentação consistente da decisão e da extração clínica."""
import json
import streamlit as st
from presentation.web.components.clinical_card import renderizar_resumo_clinico
from presentation.web.components.documentos import estado_documento
from presentation.web.components.layout import nome_destino


def campos_nao_identificados(dados):
    """Ausência de informação registrada, sem inferir ilegibilidade ou obrigação."""
    campos = []
    for grupo, chave, rotulo in [
        ("paciente", "nome", "Nome do paciente"),
        ("paciente", "idade", "Idade do paciente"),
        ("medico_solicitante", "nome", "Nome do profissional solicitante"),
        ("medico_solicitante", "crm", "CRM do profissional solicitante"),
    ]:
        valor = (dados.get(grupo) or {}).get(chave)
        if valor is None or isinstance(valor, str) and not valor.strip():
            campos.append(rotulo)
    return campos


def resumo_triagem(doc):
    classificacao = doc.get("classificacao") or {}
    falha = bool(doc.get("erro_extracao"))
    score = classificacao.get("score_confianca_classificacao")
    with st.container(border=True):
        st.subheader("Resumo da triagem", icon=":material/summarize:")
        st.caption("Documento: " + str(doc.get("documento_id", "Não informado")))
        with st.container(horizontal=True):
            valores = [
                ("Categoria", "Não avaliada" if falha else classificacao.get("tipo_documento") or "Não identificada"),
                ("Especialidade", "Não avaliada" if falha else classificacao.get("especialidade") or "Não identificada"),
                ("Confiança da classificação", "Não avaliada" if falha else f"{score:.1%}" if isinstance(score, (int, float)) and 0 <= score <= 1 else "Não informada"),
                ("Origem", str(doc.get("canal_origem") or "Não registrada").replace("_", " ")),
            ]
            for rotulo, valor in valores:
                with st.container(border=True, width=220):
                    st.caption(rotulo)
                    st.text(valor)
        st.caption("A confiança é uma estimativa do modelo para a classificação; não comprova correção clínica.")
        if falha:
            return
        pendentes = campos_nao_identificados(doc.get("dados_extraidos") or {})
        revisao = bool((doc.get("decisao_roteamento") or {}).get("requer_auditoria_humana"))
        if pendentes:
            st.markdown("**Campos não identificados no resultado**")
            for campo in pendentes:
                st.text("• " + campo)
            st.caption("Ausência no resultado não comprova ausência no original ou ilegibilidade. A necessidade desses campos depende do documento.")
        if revisao:
            st.warning("Revisão humana necessária. Confira os dados e a justificativa de encaminhamento abaixo.")
        elif not pendentes:
            st.caption("Identificação do paciente e do profissional preenchida no resultado; conteúdo ainda sujeito à conferência.")


def exibir_resultado(doc):
    if doc.get("acompanhamento_fluxo_confirmado") is False:
        st.warning("A triagem retornou, mas a última etapa do quadro não pôde ser confirmada. Atualize as filas antes de reenviar.")
    estado = estado_documento(doc)
    cores = {"Falha na extração": "red", "Erro": "red", "Aguardando revisão": "orange", "Processado": "green"}
    st.badge(estado, color=cores.get(estado, "gray"))
    resumo_triagem(doc)
    if doc.get("erro_extracao"):
        st.error("Extração não realizada: " + doc["erro_extracao"]["mensagem"])
        st.caption("A prioridade clínica não foi avaliada. Documento encaminhado para revisão humana.")
    else:
        renderizar_resumo_clinico(doc.get("dados_extraidos", {}), doc.get("classificacao", {}))
    decisao = doc.get("decisao_roteamento", {})
    with st.container(border=True):
        st.subheader("Encaminhamento", icon=":material/route:")
        st.write("**Destino:**", nome_destino(decisao.get("destino_principal")))
        mensagem = decisao.get("justificativa_roteamento") or "Sem justificativa informada."
        if decisao.get("requer_auditoria_humana"):
            st.warning(mensagem)
            st.page_link("app_pages/auditoria.py", label="Abrir revisão humana", icon=":material/fact_check:")
        elif doc.get("classificacao", {}).get("nivel_prioridade") == "Urgente":
            st.error(mensagem)
        else:
            st.info(mensagem)
        armazenamento = doc.get("armazenamento_oci", {})
        if armazenamento.get("status_backup") == "falha":
            st.error("Falha ao salvar o resultado da triagem.")
        elif armazenamento.get("status_backup") == "sucesso":
            st.caption("Armazenamento confirmado pelo serviço de triagem.")
        if decisao.get("notificacao_gerada"):
            st.caption("Alerta gerado. A entrega externa não é comprovada por este registro.")
    with st.expander("Dados estruturados e armazenamento", icon=":material/data_object:"):
        st.caption(f"Objeto: {armazenamento.get('caminho_objeto', 'Não informado')}")
        st.json(doc)
    st.download_button("Baixar resultado JSON", json.dumps(doc, ensure_ascii=False, indent=2), file_name=f"{doc.get('documento_id', 'triagem')}.json", mime="application/json", icon=":material/download:")
