"""
Entidade de Domínio: Paciente
Responsável por encapsular as regras de negócio e dados demográficos fundamentais.
Não depende de frameworks externos ou adaptadores de infraestrutura.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional
import re


@dataclass
class Paciente:
    """
    Entidade que representa o paciente no fluxo de triagem clínica do MediFlow.
    """
    nome: str
    idade: Optional[int] = None
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    sexo: Optional[str] = None  # 'M', 'F', 'Outro' ou None

    def __post_init__(self) -> None:
        self._sanitizar_nome()
        self._validar_idade()
        if self.cpf:
            self._validar_e_formatar_cpf()

    def _sanitizar_nome(self) -> None:
        """Limpa espaços extras e valida se o nome não é vazio."""
        if not self.nome or not self.nome.strip():
            raise ValueError("O nome do paciente é obrigatório e não pode ser vazio.")
        self.nome = " ".join(self.nome.strip().split())

    def _validar_idade(self) -> None:
        """Garante consistência biológica da idade."""
        if self.idade is not None:
            if not isinstance(self.idade, int) or self.idade < 0 or self.idade > 130:
                raise ValueError(f"Idade inválida ({self.idade}). Deve ser um valor inteiro entre 0 e 130 anos.")

    def _validar_e_formatar_cpf(self) -> None:
        """
        Remove caracteres não numéricos do CPF e valida quantidade de dígitos.
        Para um MVP, garante que possui 11 dígitos numéricos se fornecido.
        """
        digitos = re.sub(r"\D", "", str(self.cpf))
        if len(digitos) != 11:
            raise ValueError(f"CPF inválido ({self.cpf}). Deve conter exatamente 11 dígitos.")
        self.cpf = f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"

    @property
    def is_demograficamente_completo(self) -> bool:
        """
        Regra de negócio: verifica se o paciente possui dados suficientes
        para vinculação automática com o Prontuário Eletrónico (PEP).
        """
        return bool(self.nome and (self.idade is not None or self.data_nascimento or self.cpf))

    @property
    def is_populacao_vulneravel(self) -> bool:
        """
        Regra clínica: identifica se o paciente pertence a faixas etárias de atenção prioritária
        (pediátricos ou idosos >= 60 anos).
        """
        if self.idade is not None:
            return self.idade < 12 or self.idade >= 60
        return False

    def calcular_idade_a_partir_nascimento(self, referencia: Optional[date] = None) -> Optional[int]:
        """Calcula ou atualiza a idade a partir da data de nascimento se informada."""
        if not self.data_nascimento:
            return self.idade
        
        hoje = referencia or date.today()
        anos = hoje.year - self.data_nascimento.year
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            anos -= 1
        
        self.idade = max(0, anos)
        return self.idade