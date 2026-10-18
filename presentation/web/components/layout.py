"""Padrões visuais compartilhados pelas páginas operacionais."""
import streamlit as st


DESTINOS = {
    "Prontuario_Eletronico_Paciente": "Prontuário eletrônico",
    "Farmacia_Hospitalar": "Farmácia hospitalar",
    "Auditoria_de_Autorizacoes": "Auditoria de autorizações",
    "Fila_Emergencia_Medica": "Emergência médica",
    "Auditoria_Humana": "Revisão humana",
}


def nome_destino(valor):
    return DESTINOS.get(valor, (valor or "Não informado").replace("_", " "))


def cabecalho(titulo, descricao, secao="Triagem"):
    st.caption(f"{secao} › {titulo}")
    st.title(titulo)
    st.caption(descricao)


def indicadores(itens):
    if len(itens) == 4:
        for coluna, (rotulo, valor) in zip(st.columns(4), itens):
            coluna.metric(rotulo, valor, border=True, height="stretch")
        return
    with st.container(horizontal=True):
        for rotulo, valor in itens:
            st.metric(rotulo, valor, border=True, width=220)


def estado_vazio(titulo, descricao, icone=":material/folder_open:", nova_triagem=False):
    with st.container(border=True, horizontal_alignment="center"):
        st.subheader(titulo, icon=icone)
        st.caption(descricao)
        if nova_triagem:
            st.page_link("app_pages/nova_triagem.py", label="Nova triagem", icon=":material/add_circle:")


def etapas_triagem(documento=None):
    """O serviço retorna classificação e extração juntas; não simula progresso."""
    finalizado = documento is not None
    falha = bool(documento and documento.get("erro_extracao"))
    etapas = [
        ("1 · Recebimento", "Documento enviado" if finalizado else "Envie um documento", ":material/upload_file:"),
        ("2 · Classificação", "Não realizada" if falha else "Classificação disponível" if finalizado else "Identificação do tipo", ":material/category:"),
        ("3 · Extração e validação", "Revisão necessária" if falha else "Dados extraídos" if finalizado else "Conferência dos campos", ":material/fact_check:"),
        ("4 · Resultado", "Encaminhamento disponível" if finalizado else "Destino e justificativa", ":material/route:"),
    ]
    for coluna, (titulo, descricao, icone) in zip(st.columns(4), etapas):
        with coluna.container(border=True, height="stretch"):
            st.markdown(f"{icone} **{titulo}**")
            st.caption(descricao)
