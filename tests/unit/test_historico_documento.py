from unittest.mock import patch
import requests
from streamlit.testing.v1 import AppTest
from presentation.web.components.historico import horario_evento, registro_do_documento


def test_horarios_nao_inventam_fuso_e_normalizam_utc():
    assert horario_evento(None) == "Horário não registrado"
    assert horario_evento("inválido") == "Horário indisponível"
    assert horario_evento("2026-10-18T12:00:00-03:00") == "18/10/2026 15:00:00 UTC"
    assert "fuso não registrado" in horario_evento("2026-10-18T12:00:00")


def test_nao_mistura_eventos_de_execucoes_distintas():
    assert registro_do_documento([{"documento_id": "A", "execucao_id": "anterior"}], {"documento_id": "A", "execucao_id": "atual"}) is None


def executar(resposta=None, erro=None):
    with patch("presentation.web.components.historico.consultar", return_value=resposta, side_effect=erro):
        return AppTest.from_string('''
from presentation.web.components.historico import exibir_historico
exibir_historico({"documento_id": "A", "execucao_id": "atual"})
''', default_timeout=30).run()


def test_eventos_reconciliados_e_indisponibilidade():
    app = executar([{"documento_id": "A", "execucao_id": "atual", "eventos": [{"etapa": "recebidos", "em": None}], "registro_reconciliado": True, "etapa": "encaminhados"}])
    assert not app.exception
    assert any("Documento recebido" in m.value for m in app.markdown)
    assert any("Horário não registrado" in c.value for c in app.caption)
    assert any("horário da transição não registrado" in i.value for i in app.info)
    app = executar([])
    assert any("Histórico de etapas não disponível" in i.value for i in app.info)
    app = executar(erro=requests.ConnectionError())
    assert not app.exception
    assert any("resultado do documento continua disponível" in w.value for w in app.warning)
