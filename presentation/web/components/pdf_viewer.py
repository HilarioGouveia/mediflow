"""
Componente Visual: Visualizador de Documentos (PDF / Imagem)
Renderiza PDFs embutidos em Base64 através de um container HTML responsivo
e imagens digitalizadas com suporte a zoom nativo.
"""

import streamlit as st
import base64
from typing import Union


def renderizar_visualizador_documento(conteudo: Union[bytes, str], tipo_arquivo: str, altura: int = 580) -> None:
    """
    Renderiza o documento clínico (PDF ou imagem) embutido no layout do Streamlit.

    :param conteudo: Bytes brutos do arquivo ou string codificada em Base64.
    :param tipo_arquivo: 'PDF', 'IMAGEM' ou 'TEXTO'.
    :param altura: Altura em pixels do container de visualização.
    """
    if not conteudo:
        st.info("Nenhum arquivo físico disponível para visualização.")
        return

    # Normalizar para Base64 caso venha em bytes
    if isinstance(conteudo, (bytes, bytearray)):
        b64_str = base64.b64encode(conteudo).decode("utf-8")
    else:
        b64_str = str(conteudo)

    tipo = tipo_arquivo.upper()

    if tipo == "PDF":
        pdf_display = f"""
            <iframe 
                src="data:application/pdf;base64,{b64_str}#toolbar=0&navpanes=0&scrollbar=1" 
                width="100%" 
                height="{altura}px" 
                type="application/pdf"
                style="border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)

    elif tipo in ["IMAGEM", "IMAGE", "JPG", "JPEG", "PNG"]:
        imagem_bytes = base64.b64decode(b64_str)
        st.image(
            imagem_bytes, 
            caption="Documento Digitalizado / Exame de Imagem", 
            use_container_width=True
        )

    else:
        # Fallback para texto bruto ou formatos não renderizáveis diretamente
        st.text_area(
            label="Conteúdo do Documento",
            value=conteudo if isinstance(conteudo, str) else conteudo.decode("utf-8", errors="ignore"),
            height=altura,
            disabled=True
        )