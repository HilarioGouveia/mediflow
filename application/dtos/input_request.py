from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TipoArquivoEnum(str, Enum):
    PDF = "PDF"
    IMAGEM = "IMAGEM"
    JSON = "JSON"
    TEXTO = "TEXTO"


class TriagemRequestDTO(BaseModel):
    """Schema de entrada para requisição de processamento clínico."""
    documento_id: str = Field(
        ..., 
        description="Identificador único do documento", 
        examples=["DOC-CLIN-2026-8942"]
    )
    tipo_arquivo: TipoArquivoEnum = Field(
        ..., 
        description="Formato do arquivo enviado"
    )
    documento_texto: Optional[str] = Field(
        None, 
        description="Conteúdo textual bruto extraído ou enviado diretamente"
    )
    arquivo_base64: Optional[str] = Field(
        None, 
        description="Payload binário codificado em Base64 para PDFs digitalizados ou imagens"
    )
    canal_origem: str = Field(
        ..., 
        description="Origem da solicitação", 
        examples=["Pronto_Socorro", "Ambulatorio", "Recepcao"]
    )