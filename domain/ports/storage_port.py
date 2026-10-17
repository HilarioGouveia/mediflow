# domain/ports/storage_port.py
from abc import ABC, abstractmethod
from typing import Any, Union, Dict, List

class StoragePort(ABC):
    """Porta para interação com o OCI Object Storage Always Free."""

    @abstractmethod
    def salvar_arquivo(self, bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Persiste um objeto e retorna o caminho/URI de confirmação."""
        pass

    @abstractmethod
    def salvar_json(self, bucket_name: str, object_name: str, json_data: Union[Dict[str, Any], List[Any], str]) -> bool:
        """Salva metadados e decisões estruturadas na pasta de status apropriada."""
        pass