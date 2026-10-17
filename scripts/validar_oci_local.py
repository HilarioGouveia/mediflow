"""Grava ou confere um marcador sintético após reiniciar o emulador."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from infrastructure.adapters.oci_storage_adapter import OCIStorageAdapter
from infrastructure.oci_client.storage_factory import criar_config_emulador, LOCAL_TENANCY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=["gravar", "conferir"])
    parser.add_argument("--endpoint", default="http://localhost:4599")
    args = parser.parse_args()
    storage = OCIStorageAdapter(criar_config_emulador(args.endpoint), "", args.endpoint)
    storage.namespace = storage.client.get_namespace().data
    bucket = "mediflow-testes-integracao"
    chave = "validacao/persistencia.json"
    esperado = {"teste": "persistencia-local", "dados": "sinteticos"}
    if args.acao == "gravar":
        storage.garantir_bucket(bucket, LOCAL_TENANCY)
        storage.salvar_json(bucket, chave, esperado)
    if storage.obter_json(bucket, chave) != esperado:
        raise RuntimeError("Marcador de persistência não encontrado ou divergente.")
    print("OK:", args.acao, "- marcador persistido via SDK OCI nativo.")


if __name__ == "__main__":
    main()
