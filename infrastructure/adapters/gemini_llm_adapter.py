"""
Adaptador de Infraestrutura: Gemini LLM Adapter
Implementa a porta LLMPort utilizando o SDK oficial Google GenAI.
Suporta inferência multimodal (PDF, imagens, texto plano) e Structured Outputs estritos.
"""

import base64
import binascii
import logging
from typing import Any, Dict, List

from google import genai
from google.genai import types

from domain.ports.llm_port import LLMPort
from infrastructure.adapters.schemas_llm import ExtracaoClinicaLLMSchema

logger = logging.getLogger("MediFlowGeminiAdapter")


class GeminiLLMAdapter(LLMPort):
    """
    Adaptador concreto para integração com os modelos multimodais da família Google Gemini.
    Implementa a extração padronizada via schema Pydantic (ExtracaoClinicaLLMSchema).
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def _obter_system_instruction(self) -> str:
        return (
            "És um assistente clínico de triagem médica de alta precisão do sistema MediFlow. "
            "A tua função é analisar documentos médicos (PDFs digitais/digitalizados, fotos de receitas, "
            "laudos de exames ou texto bruto), classificar a sua categoria documental e extrair dados vitais. "
            "Regras mandatórias:\n"
            "1. Atribui score_confianca baixo (< 0.85) se houver rasuras, letras ilegíveis, imagens borradas "
            "ou falta do nome do paciente e CRM.\n"
            "2. Identifica sinais de urgência com rigor absoluto. Define achado_critico=True e "
            "nivel_prioridade='Urgente' perante risco de morte iminente (ex.: TEP agudo, AVC, Enfarte, choque).\n"
            "3. Garante conformidade estrita com o schema JSON configurado."
        )

    def _preparar_partes_multimodais(self, conteudo: Any, tipo_arquivo: str) -> List[Any]:
        """
        Processa com segurança o conteúdo recebido (bytes, string base64 ou texto puro)
        e constrói as partes compatíveis com a API do Gemini.
        """
        tipo = (tipo_arquivo or "TEXTO").strip().upper()
        partes: List[Any] = []

        if tipo in ["PDF", "IMAGEM"]:
            bytes_conteudo: bytes = b""

            # Tratamento defensivo de conversão binária / base64
            if isinstance(conteudo, (bytes, bytearray)):
                bytes_conteudo = bytes(conteudo)
            elif isinstance(conteudo, str):
                try:
                    bytes_conteudo = base64.b64decode(conteudo, validate=True)
                except (binascii.Error, ValueError):
                    logger.warning(
                        "Conteúdo marcado como %s não é um Base64 válido. Tratando como texto plano.",
                        tipo
                    )
                    bytes_conteudo = b""

            if bytes_conteudo:
                mime_type = "application/pdf" if tipo == "PDF" else "image/jpeg"
                partes.append(
                    types.Part.from_bytes(
                        data=bytes_conteudo,
                        mime_type=mime_type,
                    )
                )
                partes.append(
                    "Analisa minuciosamente o documento médico anexo e extrai rigorosamente todas as entidades clínicas."
                )
                return partes

        # Fallback para processamento textual direto
        texto_limpo = conteudo if isinstance(conteudo, str) else str(conteudo)
        partes.append(f"Analisa o seguinte registro clínico e extrai as entidades estruturadas:\n\n{texto_limpo}")
        return partes

    def processar_documento(self, conteudo: Any, tipo_arquivo: str) -> Dict[str, Any]:
        """
        Ingere o documento clínico e retorna o dicionário serializado compatível com o domínio.
        """
        partes = self._preparar_partes_multimodais(conteudo, tipo_arquivo)

        config = types.GenerateContentConfig(
            system_instruction=self._obter_system_instruction(),
            temperature=0.1,  # Determinação estrita sem variações criativas
            response_mime_type="application/json",
            response_schema=ExtracaoClinicaLLMSchema,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=partes,
                config=config,
            )

            # Extração validada diretamente via objeto parsed do SDK
            resultado_estruturado: ExtracaoClinicaLLMSchema = response.parsed
            if resultado_estruturado is None:
                raise ValueError("O modelo não devolveu um payload estruturado válido.")

            return resultado_estruturado.model_dump()

        except Exception as exc:
            logger.error("Falha na chamada ao modelo Gemini (%s): %s", self.model_name, exc)
            # Retorno de contingência com baixa confiança para desvio para auditoria humana
            return {
                "tipo_documento": "Documento Clínico Não Identificado",
                "especialidade": "Clínica Geral",
                "nivel_prioridade": "Rotina",
                "score_confianca": 0.0,
                "paciente": {"nome": None, "idade": None},
                "medico_solicitante": {"nome": None, "crm": None},
                "exame_realizado": None,
                "diagnostico_principal": None,
                "cid_sugerido": None,
                "medicamentos": [],
                "achado_critico": False,
            }