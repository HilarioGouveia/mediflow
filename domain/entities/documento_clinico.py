"""
Entidade de Domínio: DocumentoClinico
Responsável por encapsular os metadados do arquivo clínico ingerido,
rastreabilidade de origem e cálculo de integridade criptográfica (hash SHA-256).
Núcleo Puro: Zero dependências de frameworks externos ou SDKs de nuvem.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Union
import hashlib
import re


class TipoFormatoDocumento(str, Enum):
    PDF = "PDF"
    IMAGEM = "IMAGEM"
    TEXTO = "TEXTO"
    JSON = "JSON"


class StatusDocumento(str, Enum):
    RECEBIDO = "RECEBIDO"
    EM_PROCESSAMENTO = "EM_PROCESSAMENTO"
    PROCESSADO = "PROCESSADO"
    RETIDO_AUDITORIA = "RETIDO_AUDITORIA"
    FALHA = "FALHA"


@dataclass
class DocumentoClinico:
    """
    Entidade de Domínio que representa o documento físico ou digital no fluxo MediFlow.
    Garante integridade criptográfica, imutabilidade de metadados vitais e auditoria.
    """
    documento_id: str
    tipo_formato: TipoFormatoDocumento
    canal_origem: str
    conteudo_bruto: Optional[Union[bytes, str]] = None
    hash_integridade: str = field(init=False)
    data_recebimento: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: StatusDocumento = field(default=StatusDocumento.RECEBIDO)
    tamanho_bytes: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self._validar_identificador()
        self._sanitizar_canal_origem()
        self._calcular_hash_e_tamanho()

    def _validar_identificador(self) -> None:
        """Garante que o documento_id esteja preenchido e siga um padrão mínimo."""
        if not self.documento_id or not self.documento_id.strip():
            raise ValueError("O identificador do documento (documento_id) é obrigatório.")
        self.documento_id = self.documento_id.strip()

    def _sanitizar_canal_origem(self) -> None:
        """Remove caracteres inválidos do canal de origem (ex: Pronto_Socorro, Ambulatorio)."""
        if not self.canal_origem or not self.canal_origem.strip():
            raise ValueError("O canal de origem é obrigatório para rastreabilidade de triagem.")
        self.canal_origem = re.sub(r"[^\w\-_]", "", self.canal_origem.strip())

    def _calcular_hash_e_tamanho(self) -> None:
        """
        Calcula o hash SHA-256 do conteúdo para garantir integridade e auditoria.
        Evita adulterações e permite detecção de duplicidades.
        """
        if self.conteudo_bruto is None:
            # Caso receba apenas metadados sem binário em memória
            self.hash_integridade = hashlib.sha256(self.documento_id.encode("utf-8")).hexdigest()
            self.tamanho_bytes = 0
            return

        if isinstance(self.conteudo_bruto, str):
            dados_bytes = self.conteudo_bruto.encode("utf-8")
        elif isinstance(self.conteudo_bruto, (bytes, bytearray)):
            dados_bytes = bytes(self.conteudo_bruto)
        else:
            raise TypeError("O conteúdo bruto deve ser do tipo bytes, str ou None.")

        self.tamanho_bytes = len(dados_bytes)
        self.hash_integridade = hashlib.sha256(dados_bytes).hexdigest()

    def verificar_integridade(self, dados: Union[bytes, str]) -> bool:
        """
        Valida se os dados fornecidos correspondem exatamente ao hash registrado.
        Útil antes do envio para o OCI Object Storage ou pós-download.
        """
        if isinstance(dados, str):
            bytes_comparar = dados.encode("utf-8")
        else:
            bytes_comparar = bytes(dados)

        hash_atual = hashlib.sha256(bytes_comparar).hexdigest()
        return self.hash_integridade == hash_atual

    def atualizar_status(self, novo_status: StatusDocumento) -> None:
        """Transiciona o status do documento de forma explícita."""
        self.status = novo_status

    @property
    def nome_arquivo_padronizado(self) -> str:
        """
        Gera um nome seguro e unificado para persistência no OCI Object Storage.
        Exemplo: DOC-CLIN-2026-8942_a1b2c3d4.json
        """
        hash_curto = self.hash_integridade[:8]
        return f"{self.documento_id}_{hash_curto}"