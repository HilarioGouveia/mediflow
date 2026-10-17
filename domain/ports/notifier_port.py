from abc import ABC, abstractmethod


class NotifierPort(ABC):
    """Porta para emissão de alertas em tempo real."""

    @abstractmethod
    def enviar_alerta_urgencia(self, canal: str, mensagem: str) -> bool:
        """Dispara mensagem para canal de plantão médico ou sistema de mensageria."""
        pass