"""Login OIDC nativo e autorização de acesso ao painel."""
import os
import time
import streamlit as st


def auth_habilitada():
    valor = os.getenv("AUTH_ENABLED", "false").strip().lower()
    if valor not in {"true", "false", "1", "0"}:
        raise ValueError("AUTH_ENABLED deve ser true ou false.")
    return valor in {"true", "1"}


def email_autorizado(usuario, permitidos):
    return (usuario.get("email_verified") is True
            and str(usuario.get("email", "")).strip().casefold() in permitidos)


def exigir_login():
    try:
        habilitada = auth_habilitada()
    except ValueError:
        st.error("Configuração de autenticação inválida. Consulte o administrador.")
        st.stop()
    if not habilitada:
        return False
    if not st.user.is_logged_in:
        st.title(":material/health_and_safety: MediFlow")
    permitidos = {email.strip().casefold() for email in os.getenv("AUTH_ALLOWED_EMAILS", "").split(",") if email.strip()}
    if len(os.getenv("MEDIFLOW_API_TOKEN", "")) < 32 or not permitidos:
        st.error("Acesso ainda não configurado. Defina a credencial da API e os e-mails autorizados no servidor.")
        st.stop()
    try:
        auth = st.secrets["auth"]
        provedor = os.getenv("AUTH_PROVIDER", "google")
        provider = auth[provedor]
        pronto = all(auth.get(k) for k in ("redirect_uri", "cookie_secret")) and all(provider.get(k) for k in ("client_id", "client_secret", "server_metadata_url"))
        if not pronto:
            raise ValueError("Configuração incompleta")
    except (FileNotFoundError, KeyError, ValueError):
        st.error("Login OIDC ainda não configurado. Preencha o arquivo de secrets do Streamlit no servidor.")
        st.stop()
    if not st.user.is_logged_in:
        st.caption("Triagem documental clínica")
        with st.container(border=True):
            st.subheader("Bem-vindo ao MediFlow")
            st.write("Entre com sua conta autorizada para acessar os documentos e as filas de processamento.")
            rotulo = "Continuar com Google" if provedor == "google" else "Entrar com o provedor de identidade"
            if st.button(rotulo, icon=":material/login:", type="primary", width="stretch"):
                st.login(provedor)
        st.stop()
    if not email_autorizado(st.user, permitidos):
        st.error("Esta conta não possui acesso autorizado ao MediFlow.")
        if st.button("Sair desta conta", icon=":material/logout:"):
            st.session_state.clear()
            st.logout()
        st.stop()
    expiracao = st.user.get("exp")
    if expiracao is not None and float(expiracao) <= time.time():
        st.session_state.clear()
        st.logout()
        st.stop()
    with st.sidebar:
        st.caption("Conectado como " + str(st.user.get("email", "")))
        if st.button("Sair", icon=":material/logout:", width="stretch"):
            st.session_state.clear()
            st.logout()
            st.stop()
    return True
