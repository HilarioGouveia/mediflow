from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMPort(ABC):
    """Porta para extração multimodal e inferência diagnóstica."""

    @abstractmethod
    def processar_documento(self, conteudo: Any, tipo_arquivo: str) -> Dict[str, Any]:
        """Classifica e extrai entidades clínicas estruturadas a partir de texto, PDF ou imagem."""
        pass