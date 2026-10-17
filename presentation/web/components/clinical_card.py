"""
Componente Visual: Cartão de Resumo Clínico & Badges de Triagem
Padroniza a apresentação das entidades clínicas extraídas pela LLM Multimodal.
"""

import streamlit as st
from typing import Dict, Any, Optional


def renderizar_badge_score(score: float) -> str:
    """
    Gera tag visual com cor semântica baseada na confiabilidade:
    - Verde: >= 0.85 (Confiável para automação)
    - Amarelo: 0.70 a 0.84 (Risco de inconsistência moderado)
    - Vermelho: < 0.70 (Crítico / Ambiguidade severa)
    """
    porcentagem = score * 100
    if score >= 0.85:
        cor = "#28a745"
        texto = f"Alta Confiabilidade ({porcentagem:.1f}%)"
    elif score >= 0.70:
        cor = "#ffc107"
        texto = f"Confiabilidade Moderada ({porcentagem:.1f}%)"
    else:
        cor = "#dc3545"
        texto = f"Baixa Confiabilidade ({porcentagem:.1f}%)"

    return f"""
        <span style="
            background-color: {cor}; 
            color: {'#000' if score >= 0.70 and score < 0.85 else '#fff'}; 
            padding: 4px 10px; 
            border-radius: 12px; 
            font-size: 0.85rem; 
            font-weight: 600;">
            {texto}
        </span>
    """


def renderizar_resumo_clinico(dados_extraidos: Dict[str, Any], classificacao: Dict[str, Any]) -> None:
    """
    Renderiza um painel estético e estruturado com os dados do paciente,
    diagnóstico principal, especialidade médica e posologias farmacológicas.
    """
    prioridade = classificacao.get("nivel_prioridade", "Rotina")
    tipo_doc = classificacao.get("tipo_documento", "Não identificado")
    especialidade = classificacao.get("especialidade", "Geral")
    score = classificacao.get("score_confianca_classificacao", 0.0)

    # Identificação visual de emergência
    badge_cor_prioridade = "🔴" if prioridade == "Urgente" else ("🟡" if prioridade == "Prioritário" else "🟢")

    with st.container(border=True):
        col_topo1, col_topo2 = st.columns([2, 1])
        with col_topo1:
            st.markdown(f"#### {badge_cor_prioridade} {tipo_doc} — `{especialidade}`")
        with col_topo2:
            st.markdown(renderizar_badge_score(score), unsafe_allow_html=True)

        st.divider()

        # Grid de Entidades Clínicas
        col_paciente, col_medico = st.columns(2)
        
        paciente = dados_extraidos.get("paciente", {})
        medico = dados_extraidos.get("medico_solicitante", {})

        with col_paciente:
            st.markdown("**👤 Dados do Paciente:**")
            nome = paciente.get("nome") or "Não identificado"
            idade = f"{paciente.get('idade')} anos" if paciente.get("idade") is not None else "Idade não informada"
            st.write(f"• **Nome:** {nome}")
            st.write(f"• **Faixa Etária:** {idade}")

        with col_medico:
            st.markdown("**🩺 Profissional Solicitante:**")
            med_nome = medico.get("nome") or "Não identificado"
            crm = medico.get("crm") or "CRM não localizado"
            st.write(f"• **Médico:** {med_nome}")
            st.write(f"• **Registro:** `{crm}`")

        st.write("")
        # Diagnóstico e CID
        diagnostico = dados_extraidos.get("diagnostico_principal") or "Sem diagnóstico explícito"
        cid = dados_extraidos.get("cid_sugerido") or "N/A"
        
        st.markdown(f"**🔬 Hipótese Diagnóstica / Achado:** {diagnostico}")
        st.markdown(f"**🏷️ CID-10 Sugerido:** `{cid}`")

        # Medicamentos e Prescrições
        medicamentos = dados_extraidos.get("medicamentos", [])
        if medicamentos:
            st.markdown("**💊 Medicamentos Prescritos / Posologias:**")
            for med in medicamentos:
                st.markdown(f"- `{med}`")