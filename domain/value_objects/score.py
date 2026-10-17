from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreConfianca:
    valor: float

    def __post_init__(self):
        if not (0.0 <= self.valor <= 1.0):
            raise ValueError("O score de confiança deve estar entre 0.0 e 1.0.")

    @property
    def is_confiavel(self) -> bool:
        """Limiar canônico: scores abaixo de 0.85 demandam auditoria humana."""
        return self.valor >= 0.85