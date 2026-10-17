from dataclasses import dataclass, field
from typing import Optional
from domain.value_objects.score import ScoreConfianca


@dataclass
class TriagemClinica:
    documento_id: str
    tipo_documento: str
    especialidade: str
    score: ScoreConfianca
    achado_critico: bool
    paciente_nome: Optional[str] = None
    cid: Optional[str] = None
    requer_auditoria: bool = field(init=False)
    destino: str = field(init=False)
    justificativa: str = field(init=False)

    def __post_init__(self):
        self.avaliar_roteamento()

    def avaliar_roteamento(self) -> None:
        """Regra de negócio pura para definição de fluxo condicional."""
        if not self.score.is_confiavel or not self.paciente_nome:
            self.requer_auditoria = True
            self.destino = "Fila_Revisao_Humana"
            self.justificativa = "Baixo score de confiança ou ausência de dados cadastrais vitais."
        elif self.achado_critico:
            self.requer_auditoria = False
            self.destino = "Fila_Emergencia_Medica"
            self.justificativa = "Achado crítico de alta gravidade detectado em documento clínico."
        else:
            self.requer_auditoria = False
            self.destino = "Prontuario_Eletronico_Paciente"
            self.justificativa = "Fluxo padrão validado com alta confiabilidade clínica."