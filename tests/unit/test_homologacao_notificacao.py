from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from presentation.api.routers.triagem_router import (
    HomologacaoAuditoriaDTO,
    homologar_documento_auditoria,
)


@pytest.mark.parametrize(
    "destino,decisao,persistido,retorno,excecao,esperado",
    [
        ("Fila_Emergencia_Medica", "aprovar", True, True, False, True),
        ("Fila_Emergencia_Medica", "aprovar", True, False, False, False),
        ("Fila_Emergencia_Medica", "aprovar", True, True, True, False),
        ("Farmacia_Hospitalar", "aprovar", True, True, False, None),
        ("Fila_Emergencia_Medica", "rejeitar", True, True, False, None),
        ("Fila_Emergencia_Medica", "aprovar", False, True, False, None),
    ],
)
def test_notificacao_apos_homologacao(destino, decisao, persistido, retorno, excecao, esperado):
    use_case = Mock(bucket_name="teste")
    use_case.storage.obter_json.return_value = {"documento_id": "TESTE"}
    use_case.storage.mover_objeto.return_value = persistido
    use_case.notifier.enviar_alerta_urgencia.return_value = retorno
    if excecao:
        use_case.notifier.enviar_alerta_urgencia.side_effect = RuntimeError("falha simulada")
    payload = HomologacaoAuditoriaDTO(
        documento_id="TESTE", origem_oci_path="auditoria_humana/TESTE.json",
        paciente_nome="Paciente Teste", crm_retificado="12345-SP",
        diagnostico="Teste", cid_homologado="Z00", destino_aprovado=destino,
        parecer_auditor="Teste sintetico", decisao=decisao,
    )
    if not persistido:
        with pytest.raises(HTTPException) as error:
            homologar_documento_auditoria(payload, use_case)
        assert error.value.status_code == 500
        use_case.notifier.enviar_alerta_urgencia.assert_not_called()
        return
    result = homologar_documento_auditoria(payload, use_case)
    assert result["notificacao_enviada"] is esperado
    if esperado is None:
        use_case.notifier.enviar_alerta_urgencia.assert_not_called()
    else:
        use_case.notifier.enviar_alerta_urgencia.assert_called_once_with(
            canal="Alerta_Plantao_Medico",
            mensagem="ALERTA URGENTE: Paciente Paciente Teste despachado para emergência médica.",
        )
        chamadas = [chamada[0] for chamada in use_case.mock_calls]
        assert chamadas.index("storage.mover_objeto") < chamadas.index("notifier.enviar_alerta_urgencia")
