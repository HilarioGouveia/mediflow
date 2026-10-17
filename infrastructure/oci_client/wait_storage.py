"""Aguarda e inicializa o armazenamento antes de iniciar a API local."""
import time

from infrastructure.oci_client.storage_factory import get_storage_adapter


def main():
    for tentativa in range(20):
        try:
            storage = get_storage_adapter()
            print(f"Armazenamento pronto: {storage.modo}", flush=True)
            return
        except Exception as exc:
            print(f"Aguardando armazenamento ({tentativa + 1}/20): {type(exc).__name__}", flush=True)
            if tentativa == 19:
                raise RuntimeError("Armazenamento não ficou disponível; API não iniciada.") from None
            time.sleep(2)


if __name__ == "__main__":
    main()
