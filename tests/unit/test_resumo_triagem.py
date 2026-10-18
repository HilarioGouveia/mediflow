from streamlit.testing.v1 import AppTest

from presentation.web.components.resultado import campos_nao_identificados


def test_idade_zero_e_preservada_e_texto_vazio_identificado():
    campos = campos_nao_identificados({"paciente": {"nome": " ", "idade": 0}, "medico_solicitante": {"nome": "Profissional", "crm": "123-SP"}})
    assert campos == ["Nome do paciente"]


def executar(doc):
    app = AppTest.from_string("""
import streamlit as st
from presentation.web.components.resultado import resumo_triagem
resumo_triagem(st.session_state.documento)
""", default_timeout=30)
    app.session_state.documento = doc
    return app.run()


def test_resumo_nao_inventa_origem_e_sinaliza_revisao():
    app = executar({"documento_id": "DOC-1", "classificacao": {"tipo_documento": "Receita", "score_confianca_classificacao": 0.7}, "dados_extraidos": {}, "decisao_roteamento": {"requer_auditoria_humana": True}})
    assert not app.exception
    textos = [t.value for t in app.text]
    assert "70.0%" in textos and "Não registrada" in textos
    assert "• CRM do profissional solicitante" in textos
    assert any("Revisão humana necessária" in t.value for t in app.warning)


def test_falha_extracao_nao_apresenta_classificacao_de_contingencia_como_resultado():
    app = executar({"erro_extracao": {"codigo": "timeout"}, "classificacao": {"tipo_documento": "Receita", "score_confianca_classificacao": 0.0}})
    assert not app.exception
    textos = [t.value for t in app.text]
    assert textos.count("Não avaliada") == 3
    assert "0.0%" not in textos and "Receita" not in textos
