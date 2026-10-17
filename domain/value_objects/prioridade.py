"""
Objeto de Valor (Value Object): NivelPrioridade
Responsável por definir a taxonomia clínica de prioridade e urgência.
Núcleo Puro: Zero dependências externas ou de frameworks.
"""

from enum import Enum
from functools import total_ordering


@total_ordering
class NivelPrioridade(str, Enum):
    """
    Taxonomia oficial de prioridade do MediFlow.
    Implementa ordenação (@total_ordering) para facilitar comparações diretas de criticidade.
    """
    ROTINA = "Rotina"
    PRIORITARIO = "Prioritário"
    URGENTE = "Urgente"

    @classmethod
    def normalizar(cls, valor: str) -> "NivelPrioridade":
        """
        Interpreta e mapeia variações textuais comuns retornadas por LLMs ou OCR
        para a taxonomia canônica do sistema.
        """
        if not valor or not isinstance(valor, str):
            return cls.ROTINA

        termo = valor.strip().lower()
        if any(token in termo for token in ["urgente", "emergencia", "critico", "gravissimo", "imediato"]):
            return cls.URGENTE
        elif any(token in termo for token in ["priorit", "preferencial", "moderado", "amarelo"]):
            return cls.PRIORITARIO
        return cls.ROTINA

    @property
    def peso_criticidade(self) -> int:
        """Peso numérico para ordenação e filas de atendimento hospitalar."""
        mapa_pesos = {
            NivelPrioridade.ROTINA: 1,
            NivelPrioridade.PRIORITARIO: 2,
            NivelPrioridade.URGENTE: 3,
        }
        return mapa_pesos[self]

    def __lt__(self, outro: object) -> bool:
        if not isinstance(outro, NivelPrioridade):
            return NotImplemented
        return self.peso_criticidade < outro.peso_criticidade

    @property
    def is_urgente(self) -> bool:
        """Determina se aciona protocolo de emergência imediata."""
        return self == NivelPrioridade.URGENTE

    @property
    def sla_minutos(self) -> int:
        """
        Regra de negócio clínico: SLA máximo tolerado para triagem/despacho.
        - Urgente: até 15 minutos (Protocolo de Manchester / Emergência)
        - Prioritário: até 60 minutos
        - Rotina: até 1440 minutos (24 horas)
        """
        mapa_sla = {
            NivelPrioridade.URGENTE: 15,
            NivelPrioridade.PRIORITARIO: 60,
            NivelPrioridade.ROTINA: 1440,
        }
        return mapa_sla[self]

    @property
    def subpasta_oci(self) -> str:
        """Mapeia o nível de prioridade para a convenção de prefixo no OCI Object Storage."""
        mapa_pastas = {
            NivelPrioridade.URGENTE: "urgentes",
            NivelPrioridade.PRIORITARIO: "prioritarios",
            NivelPrioridade.ROTINA: "rotina",
        }
        return mapa_pastas[self]