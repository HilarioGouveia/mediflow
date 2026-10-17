"""Resumo dos dados clínicos extraídos."""
import streamlit as st


def renderizar_resumo_clinico(dados_extraidos, classificacao):
    prioridade = classificacao.get("nivel_prioridade", "Rotina")
    st.badge(prioridade, color="red" if prioridade == "Urgente" else "orange" if prioridade == "Prioritário" else "green")
    st.subheader(classificacao.get("tipo_documento", "Documento clínico"))
    st.caption(classificacao.get("especialidade", "Especialidade não informada"))
    st.metric("Confiança da extração", f"{classificacao.get('score_confianca_classificacao', 0):.1%}")
    paciente = dados_extraidos.get("paciente") or {}
    medico = dados_extraidos.get("medico_solicitante") or {}
    st.write("**Paciente:**", paciente.get("nome") or "Não identificado")
    if paciente.get("idade") is not None:
        st.write("**Idade:**", f"{paciente['idade']} anos")
    st.write("**Profissional:**", medico.get("nome") or "Não identificado")
    st.write("**CRM:**", medico.get("crm") or "Não informado")
    st.write("**Exame:**", dados_extraidos.get("exame_realizado") or "Não informado")
    st.write("**Diagnóstico / achado:**", dados_extraidos.get("diagnostico_principal") or "Não informado")
    st.write("**CID-10 sugerido:**", dados_extraidos.get("cid_sugerido") or "Não informado")
    medicamentos = dados_extraidos.get("medicamentos") or []
    if medicamentos:
        st.write("**Medicamentos e posologias**")
        for medicamento in medicamentos:
            st.text(str(medicamento))
