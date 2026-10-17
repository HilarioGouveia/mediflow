"""Visualização nativa do documento clínico."""
import base64
import importlib.util

import streamlit as st


def renderizar_visualizador_documento(conteudo, tipo_arquivo, altura=580):
    if not conteudo:
        st.info("Documento original não disponível.")
        return
    tipo = tipo_arquivo.upper()
    if tipo in ("PDF", "IMAGEM", "IMAGE", "JPG", "JPEG", "PNG"):
        bruto = base64.b64decode(conteudo) if isinstance(conteudo, str) else bytes(conteudo)
        if tipo == "PDF":
            if importlib.util.find_spec("streamlit_pdf"):
                st.pdf(bruto, height=altura, alt="Documento clínico original para conferência")
            else:
                st.info("Visualização PDF indisponível neste ambiente. Baixe o original para conferir.")
            st.download_button("Baixar documento original", bruto, "documento.pdf", "application/pdf")
        else:
            st.image(bruto, caption="Documento original", alt="Documento clínico enviado", width="stretch")
    else:
        st.code(conteudo if isinstance(conteudo, str) else conteudo.decode("utf-8", errors="replace"), language=None, wrap_lines=True)
