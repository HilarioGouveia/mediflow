from unittest.mock import Mock, patch

from config.settings import Settings
from infrastructure.diagnostico import diagnosticar


def configuracao(**valores):
    return Settings(_env_file=None, APP_MODE="operational", GEMINI_API_KEY="chave-de-teste", **valores)


def test_inspecao_nao_inicializa_armazenamento_nem_expoe_chave():
    cfg = configuracao(STORAGE_MODE="memory")
    with patch("infrastructure.diagnostico.settings", cfg), patch("oci.object_storage.ObjectStorageClient") as cliente:
        resultado = diagnosticar(True)
    cliente.assert_not_called()
    assert "chave-de-teste" not in str(resultado)
    assert any(i["estado"] == "aviso" and i["recurso"] == "Armazenamento" for i in resultado["itens"])


def test_chave_exemplo_impede_nova_analise():
    cfg = configuracao()
    cfg.GEMINI_API_KEY = "sua_chave_gemini"
    with patch("infrastructure.diagnostico.settings", cfg):
        assert diagnosticar()["itens"][0]["estado"] == "erro"


def test_consulta_manual_emulador_somente_leitura_e_falha_sem_segredos():
    cfg = configuracao(STORAGE_MODE="emulator")
    cliente = Mock()
    cliente.get_namespace.return_value.data = "namespace"
    with patch("infrastructure.diagnostico.settings", cfg), patch("oci.object_storage.ObjectStorageClient", return_value=cliente):
        assert diagnosticar()["itens"][1]["estado"] == "nao_verificado"
        cliente.get_bucket.assert_not_called()
        assert diagnosticar(True)["itens"][1]["estado"] == "ok"
        cliente.get_bucket.assert_called_once_with("namespace", cfg.OCI_BUCKET_NAME)
        cliente.get_bucket.side_effect = RuntimeError("segredo-interno")
        falha = diagnosticar(True)
        assert falha["itens"][1]["estado"] == "erro"
        assert "segredo-interno" not in str(falha)
        cliente.create_bucket.assert_not_called()
        cliente.put_object.assert_not_called()


def test_endpoint_independe_da_inicializacao_do_storage():
    from fastapi.testclient import TestClient
    from presentation.api.main import app
    cfg = configuracao(STORAGE_MODE="memory", AUTH_ENABLED=False)
    with patch("infrastructure.diagnostico.settings", cfg), patch("infrastructure.oci_client.storage_factory.get_storage_adapter", side_effect=RuntimeError("indisponível")) as storage:
        resposta = TestClient(app).get("/triagem/diagnostico")
        assert resposta.status_code == 200
        assert resposta.json()["itens"]
        storage.assert_not_called()
