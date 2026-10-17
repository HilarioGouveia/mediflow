from unittest.mock import MagicMock, patch
from infrastructure.adapters.gemini_llm_adapter import GeminiLLMAdapter
from infrastructure.adapters.schemas_llm import ExtracaoClinicaLLMSchema, PacienteLLMSchema, MedicoSolicitanteLLMSchema


def test_extracao_gemini_sucesso():
    # Mock do retorno da API
    mock_dados = ExtracaoClinicaLLMSchema(
        tipo_documento="Laudo de Exame de Imagem",
        especialidade="Radiologia / Pneumologia",
        nivel_prioridade="Urgente",
        score_confianca=0.99,
        paciente=PacienteLLMSchema(nome="Carlos Eduardo Mendes", idade=52),
        medico_solicitante=MedicoSolicitanteLLMSchema(nome="Dra. Renata Silveira", crm="145892-SP"),
        exame_realizado="Tomografia de Torax com contraste",
        diagnostico_principal="Tromboembolismo Pulmonar Agudo (TEP)",
        cid_sugerido="I26.9",
        medicamentos=[],
        achado_critico=True,
    )

    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.models.generate_content.return_value.parsed = mock_dados

        adapter = GeminiLLMAdapter(api_key="mock_key")
        resultado = adapter.processar_documento("Laudo de TEP agudo", "TEXTO")

        assert resultado["score_confianca"] == 0.99
        assert resultado["achado_critico"] is True
        assert resultado["diagnostico_principal"] == "Tromboembolismo Pulmonar Agudo (TEP)"
        assert resultado["paciente"]["nome"] == "Carlos Eduardo Mendes"