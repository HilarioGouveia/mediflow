"""
Objeto de Valor (Value Object): CID10
Responsável por encapsular, sanitizar e validar códigos da CID-10 (Classificação Internacional de Doenças).
Núcleo Puro: Zero dependências externas de frameworks ou bibliotecas de terceiros.
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class CID10:
    """
    Representa um código da CID-10 validado.
    Exemplos válidos: 'I26.9', 'i269', 'J18.9', 'A09', 'R07.4'.
    """
    codigo: str
    descricao: Optional[str] = None

    # Expressão regular oficial para CID-10: 
    # 1 letra (exceto U para códigos padrão, embora U exista para causas especiais), 
    # 2 dígitos numéricos e opcionalmente 1 ponto seguido de 1 ou 2 dígitos (subcategoria).
    _PADRAO_CID10 = re.compile(r"^[A-Z]\d{2}(\.\d{1,2})?$")

    def __post_init__(self) -> None:
        codigo_formatado = self._sanitizar_e_formatar(self.codigo)
        if not self._PADRAO_CID10.match(codigo_formatado):
            raise ValueError(
                f"Código CID-10 inválido: '{self.codigo}'. "
                "Deve seguir o padrão de 1 letra seguida de 2 dígitos e subcategoria opcional (ex: I26.9, J06, A09.0)."
            )
        # Atribuição em dataclass congelada (frozen) via __setattr__
        object.__setattr__(self, "codigo", codigo_formatado)
        if self.descricao:
            object.__setattr__(self, "descricao", self.descricao.strip())

    @staticmethod
    def _sanitizar_e_formatar(valor: str) -> str:
        """
        Remove espaços, converte para maiúsculas e insere o ponto na subcategoria se ausente.
        Exemplo: 'i269' -> 'I26.9', ' j18.9 ' -> 'J18.9'.
        """
        if not valor or not isinstance(valor, str):
            return ""

        limpo = re.sub(r"[^A-Za-z0-9]", "", valor).upper()
        if len(limpo) > 3 and "." not in valor:
            return f"{limpo[:3]}.{limpo[3:]}"
        return valor.strip().upper()

    @property
    def categoria(self) -> str:
        """Retorna os três primeiros caracteres que compõem o agrupamento principal (ex: 'I26')."""
        return self.codigo[:3]

    @property
    def subcategoria(self) -> Optional[str]:
        """Retorna a subcategoria após o ponto, se existir (ex: '9' em 'I26.9')."""
        partes = self.codigo.split(".")
        return partes[1] if len(partes) > 1 else None

    @property
    def is_emergencia_cardiaca_respiratoria(self) -> bool:
        """
        Regra clínica: identifica se o código pertence aos grupos de doenças do aparelho
        circulatório ou respiratório com alto potencial de complicação imediata:
        - I20 a I25: Doenças isquêmicas do coração (Infarto, Angina)
        - I26: Embolia pulmonar (TEP agudo)
        - I60 a I64: Doenças cerebrovasculares (AVC / AVE)
        - J80, J81, J96: Insuficiência respiratória e edema pulmonar agudo
        """
        capitulo = self.categoria
        letra = capitulo[0]
        numero = int(capitulo[1:]) if capitulo[1:].isdigit() else -1

        if letra == "I":
            return (20 <= numero <= 26) or (60 <= numero <= 64)
        if letra == "J":
            return numero in [80, 81, 96]
        return False

    def __str__(self) -> str:
        if self.descricao:
            return f"{self.codigo} - {self.descricao}"
        return self.codigo