"""
Módulo de Decisão Condicional (LangGraph)
Gerencia o fluxo de estados e as arestas condicionais com verificação estrita
de confiabilidade, presença de paciente, CRM válido e ausência de conflitos clínicos.
"""

from langgraph.graph import StateGraph, END
from domain.ports.llm_port import LLMPort
from application.workflows.state import WorkflowTriagemState
from application.workflows.nodes import TriagemNodes
from application.workflows.rules import requer_auditoria
from application.workflows.rules import validar_formato_crm as validar_formato_crm


def avaliar_caminho_decisao(state: WorkflowTriagemState) -> str:
    """Criticidade tem precedência; pendências continuam exigindo revisão."""
    if state.get("achado_critico", False):
        return "rota_urgencia"
    if requer_auditoria(state):
        return "rota_auditoria"
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
