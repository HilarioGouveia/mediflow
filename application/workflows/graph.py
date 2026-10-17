"""
Módulo de Decisão Condicional (LangGraph)
Gerencia o fluxo de estados e as arestas condicionais com verificação estrita
de confiabilidade, presença de paciente, CRM válido e ausência de conflitos clínicos.
"""

import re
from langgraph.graph import StateGraph, END
from domain.ports.llm_port import LLMPort
from application.workflows.state import WorkflowTriagemState
from application.workflows.nodes import TriagemNodes


def validar_formato_crm(crm: str) -> bool:
    """
    Valida se o CRM possui dígitos seguidos de hífen e UF (ex: '145892-SP' ou '145892/SP').
    Permite tolerância a variações sem hífen se contiver números e estado válido.
    """
    if not crm or not isinstance(crm, str):
        return False
    
    crm_limpo = crm.strip().upper()
    # Padrão: 4 a 8 dígitos numéricos, separador opcional (- ou /) e sigla da UF (2 letras)
    padrao = re.compile(r"^\d{4,8}[-/]?[A-Z]{2}$")
    return bool(padrao.match(crm_limpo))


def avaliar_caminho_decisao(state: WorkflowTriagemState) -> str:
    """
    Função de decisão condicional (Conditional Edge):
    Determina o próximo nó com base em:
    1. Score de confiança (mínimo 0.85).
    2. Identificação mandante do paciente (nome completo e legível).
    3. Identificação mandatória do médico solicitante (CRM válido com UF).
    4. Detecção de conflitos de dados clínicos ou ausência de substância em receituários.
    5. Presença de achados clínicos críticos de emergência.
    """
    score = state.get("score_confianca", 0.0)
    dados = state.get("dados_llm") or {}
    
    # 1. Validação de Entidades Mandatórias
    paciente = dados.get("paciente") or {}
    paciente_valido = bool(paciente.get("nome") and str(paciente.get("nome")).strip())

    medico = dados.get("medico_solicitante") or {}
    crm_valor = medico.get("crm")
    crm_valido = validar_formato_crm(crm_valor)

    # 2. Avaliação de Potenciais Conflitos Clínicos
    tipo_doc = str(dados.get("tipo_documento", "")).lower()
    medicamentos = dados.get("medicamentos") or []
    exame = dados.get("exame_realizado")
    diagnostico = dados.get("diagnostico_principal")
    
    houve_conflito = False

    # Conflito A: Receituário sem nenhum fármaco ou posologia extraída
    if "receit" in tipo_doc and len(medicamentos) == 0:
        houve_conflito = True

    # Conflito B: Laudo de exame sem nome de exame e sem diagnóstico clínico
    if "laudo" in tipo_doc and not exame and not diagnostico:
        houve_conflito = True

    # 3. Regra de Fallback / Auditoria Humana (Human-in-the-Loop)
    # Se falhar score, integridade do paciente, CRM ou houver conflito de dados
    if score < 0.85 or not paciente_valido or not crm_valido or houve_conflito:
        return "rota_auditoria"

    # 4. Regra de Emergência Médica
    achado_critico = state.get("achado_critico", False)
    if achado_critico:
        return "rota_urgencia"

    # 5. Fluxo Padrão Aprovado
    return "rota_padrao"


def criar_grafo_triagem(llm_adapter: LLMPort):
    """Constrói e compila o grafo de decisão condicional do MediFlow."""
    nodes = TriagemNodes(llm_adapter)
    workflow = StateGraph(WorkflowTriagemState)

    # Definição dos nós
    workflow.add_node("extrair_informacoes", nodes.no_extracao_multimodal)
    workflow.add_node("processar_urgencia", nodes.no_avaliar_urgencia)
    workflow.add_node("processar_padrao", nodes.no_rotear_padrao)
    workflow.add_node("processar_auditoria", nodes.no_encaminhar_auditoria)

    # Ponto de entrada
    workflow.set_entry_point("extrair_informacoes")

    # Aresta condicional após extração
    workflow.add_conditional_edges(
        "extrair_informacoes",
        avaliar_caminho_decisao,
        {
            "rota_urgencia": "processar_urgencia",
            "rota_padrao": "processar_padrao",
            "rota_auditoria": "processar_auditoria",
        }
    )

    # Nós de saída terminam a execução
    workflow.add_edge("processar_urgencia", END)
    workflow.add_edge("processar_padrao", END)
    workflow.add_edge("processar_auditoria", END)

    return workflow.compile()