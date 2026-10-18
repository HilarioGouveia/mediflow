from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from infrastructure.adapters.memory_storage_adapter import MemoryStorageAdapter
from presentation.api.routers.painel_router import listar_objetos_armazenados


def test_contagens_reais_isolam_bucket_e_nao_leem_conteudo():
    storage = MemoryStorageAdapter()
    for chave in ["recebidos/a.pdf", "processados/rotina/a.json", "fluxo/a.json"]:
        storage.salvar_arquivo("teste", chave, b"conteudo")
    storage.salvar_arquivo("outro", "recebidos/b.pdf", b"conteudo")
    storage.obter_json = Mock(side_effect=AssertionError("Não deve ler conteúdo"))
    resultado = listar_objetos_armazenados(SimpleNamespace(storage=storage, bucket_name="teste"))
    assert resultado["contagens"] == {"recebidos/": 1, "processados/": 1, "auditoria_humana/": 0, "fluxo/": 1}
    assert len(resultado["objetos"]) == 3
    assert resultado["objetos"][0]["tipo"] == "PDF"
    assert resultado["objetos"][0]["caminho"] == "recebidos/a.pdf"


def test_falha_parcial_nao_retorna_contagem_enganosa_nem_segredos():
    storage = Mock()
    storage.listar_objetos_por_prefixo.side_effect = [["recebidos/a.pdf"], RuntimeError("segredo")]
    with pytest.raises(HTTPException) as erro:
        listar_objetos_armazenados(SimpleNamespace(storage=storage, bucket_name="teste"))
    assert erro.value.status_code == 503
    assert "segredo" not in erro.value.detail
