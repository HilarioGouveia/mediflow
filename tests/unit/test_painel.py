from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from infrastructure.adapters.oci_storage_adapter import OCIStorageAdapter
from infrastructure.adapters.memory_storage_adapter import MemoryStorageAdapter
from infrastructure.oci_client.client_factory import get_triagem_use_case
from presentation.api.main import app


def test_consultas_painel_e_original():
    storage = MemoryStorageAdapter()
    storage.salvar_arquivo("bucket", "recebidos/a.jpg", b"\x89PNG\r\n")
    storage.salvar_json("bucket", "processados/rotina/a.json", {"documento_id": "a"})
    storage.salvar_json("bucket", "auditoria_humana/b.json", {"documento_id": "b"})
    use_case = SimpleNamespace(storage=storage, bucket_name="bucket", notifier=SimpleNamespace(webhook_url=None))
    app.dependency_overrides[get_triagem_use_case] = lambda: use_case
    try:
        client = TestClient(app)
        assert client.get("/triagem/integracoes").json()["armazenamento"]["modo"] == "simulado"
        assert len(client.get("/triagem/historico").json()) == 2
        original = client.get("/triagem/original", params={"caminho": "recebidos/a.jpg"})
        assert original.content == b"\x89PNG\r\n"
        assert original.headers["content-type"] == "image/png"
        assert client.get("/triagem/original", params={"caminho": "processados/a.json"}).status_code == 422
        assert client.get("/triagem/original", params={"caminho": "recebidos/../a"}).status_code == 422
        assert client.get("/triagem/original", params={"caminho": "recebidos/inexistente"}).status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_listagem_oci_paginada_e_falha():
    with patch("oci.object_storage.ObjectStorageClient"):
        storage = OCIStorageAdapter({}, "teste")
    storage.client = Mock()
    storage.client.list_objects.side_effect = [
        SimpleNamespace(data=SimpleNamespace(objects=[SimpleNamespace(name="a")], next_start_with="b")),
        SimpleNamespace(data=SimpleNamespace(objects=[SimpleNamespace(name="b")], next_start_with=None)),
    ]
    assert storage.listar_objetos_por_prefixo("bucket", "processados/") == ["a", "b"]
    storage.client.list_objects.side_effect = RuntimeError("offline")
    with pytest.raises(RuntimeError):
        storage.listar_objetos_por_prefixo("bucket", "processados/")


def test_painel_offline_nao_informa_fila_vazia():
    with patch("requests.get", side_effect=requests.ConnectionError):
        painel = AppTest.from_file(Path(__file__).resolve().parents[2] / "presentation/web/app.py", default_timeout=15).run()
        assert not painel.exception
        for pagina in ("urgencias", "auditoria", "documentos", "integracoes"):
            painel.switch_page(f"app_pages/{pagina}.py").run()
            assert not painel.exception
            assert not painel.success
            assert painel.error


def test_triagem_preserva_resultado_ao_navegar():
    integracoes = {"armazenamento": {"modo": "simulado", "bucket": "teste"}, "ia": {"provedor": "Gemini", "conexao": "não verificada"}, "alertas": {"modo": "somente_log", "entrega": "não verificada"}}
    documento = {"documento_id": "DOC-1", "classificacao": {"nivel_prioridade": "Rotina", "score_confianca_classificacao": .95}, "dados_extraidos": {"paciente": {"nome": "Teste"}}, "decisao_roteamento": {"destino_principal": "Farmacia_Hospitalar", "requer_auditoria_humana": False, "justificativa_roteamento": "Receita legível"}, "armazenamento_oci": {"status_backup": "sucesso", "caminho_objeto": "processados/rotina/DOC-1.json"}}
    arquivo = SimpleNamespace(name="receita.txt", getvalue=lambda: b"Receita de teste")
    with patch("presentation.web.api_client.consultar", side_effect=lambda caminho: integracoes if caminho == "integracoes" else []), patch("presentation.web.api_client.enviar", return_value=documento) as enviar, patch("streamlit.file_uploader", return_value=arquivo):
        painel = AppTest.from_file(Path(__file__).resolve().parents[2] / "presentation/web/app.py", default_timeout=15).run()
        painel.switch_page("app_pages/nova_triagem.py").run()
        next(b for b in painel.button if b.label == "Executar triagem").click().run()
        assert not painel.exception
        enviar.assert_called_once()
        assert painel.session_state.resultado_triagem["documento_id"] == "DOC-1"
        painel.switch_page("app_pages/integracoes.py").run()
        painel.switch_page("app_pages/nova_triagem.py").run()
        assert not painel.exception
        assert painel.session_state.resultado_triagem["documento_id"] == "DOC-1"


def test_falha_ia_nao_mostra_resumo_clinico_como_sucesso():
    with patch("requests.get", side_effect=requests.ConnectionError):
        painel = AppTest.from_file(Path(__file__).resolve().parents[2] / "presentation/web/app.py", default_timeout=15).run()
        painel.session_state.resultado_triagem = {
            "status": "erro",
            "erro_extracao": {"codigo": "servico_indisponivel", "mensagem": "IA indisponível."},
            "decisao_roteamento": {"requer_auditoria_humana": True},
        }
        painel.switch_page("app_pages/nova_triagem.py").run()
        assert not painel.exception
        assert any("Extração não realizada" in erro.value for erro in painel.error)
        assert not painel.metric
