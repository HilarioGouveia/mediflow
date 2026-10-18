"""Inspeção sem inferência, alertas ou escrita no armazenamento."""
from datetime import datetime, timezone
from pathlib import Path
from config.settings import settings


def diagnosticar(conexoes=False):
    itens = []

    def item(recurso, estado, mensagem, orientacao=""):
        itens.append(dict(recurso=recurso, estado=estado, mensagem=mensagem, orientacao=orientacao))

    chave = settings.GEMINI_API_KEY.strip()
    if settings.APP_MODE == "presentation" and not settings.PRESENTATION_USE_LLM:
        item("Apresentação", "ok", "Análise simulada. Nenhuma chamada à LLM; use os arquivos de exemplo.")
    elif not chave or chave.lower() in {"sua_chave_gemini", "sua_chave_aqui"}:
        item("Gemini", "erro", "Chave ausente ou com valor de exemplo. Novas análises indisponíveis.", "Preencha GEMINI_API_KEY no .env e reinicie a API.")
    else:
        item("Gemini", "nao_verificado", "Chave preenchida; validade e cota não verificadas.")
    if settings.STORAGE_MODE == "memory":
        item("Armazenamento", "aviso", "Dados em memória: perdidos ao reiniciar a API.", "Para persistência, configure emulator ou oci.")
    else:
        try:
            import oci
            if settings.STORAGE_MODE == "oci":
                config = oci.config.from_file(str(Path(settings.OCI_CONFIG_FILE).expanduser()), settings.OCI_CONFIG_PROFILE)
                oci.config.validate_config(config)
                if not config.get("key_content") and not Path(config.get("key_file", "")).expanduser().is_file():
                    raise ValueError("Chave ausente")
            else:
                from infrastructure.oci_client.storage_factory import criar_config_emulador
                config = criar_config_emulador(settings.OCI_SERVICE_ENDPOINT)
            if not settings.OCI_NAMESPACE.strip() or not settings.OCI_BUCKET_NAME.strip():
                raise ValueError("Bucket ou namespace ausente")
        except Exception:
            item("Armazenamento", "erro", "Configuração de armazenamento inválida.", "Confira namespace e bucket. Em oci, confira arquivo, perfil e chave privada; em emulator, confira OCI_SERVICE_ENDPOINT.")
        else:
            if not conexoes:
                item("Armazenamento", "nao_verificado", "Configuração preenchida; conexão não verificada.", "Use Verificar conexões para consultar o bucket sem gravar dados.")
            else:
                try:
                    argumentos = {"service_endpoint": settings.OCI_SERVICE_ENDPOINT} if settings.STORAGE_MODE == "emulator" else {}
                    cliente = oci.object_storage.ObjectStorageClient(config, timeout=(2, 3), retry_strategy=oci.retry.NoneRetryStrategy(), **argumentos)
                    namespace = cliente.get_namespace().data if settings.STORAGE_MODE == "emulator" else settings.OCI_NAMESPACE
                    cliente.get_bucket(namespace, settings.OCI_BUCKET_NAME)
                    item("Armazenamento", "ok", "Consulta ao bucket concluída. Escrita não testada.")
                except Exception:
                    acao = "Inicie o oci-emulator e confira endpoint e bucket." if settings.STORAGE_MODE == "emulator" else "Confira rede, credenciais, namespace, bucket e permissões na OCI."
                    item("Armazenamento", "erro", "Não foi possível consultar o bucket. Operações de documentos podem falhar.", acao)
    if settings.AUTH_ENABLED:
        if len(settings.MEDIFLOW_API_TOKEN.get_secret_value()) < 32:
            item("Autenticação da API", "erro", "Token de serviço incompleto.", "Defina MEDIFLOW_API_TOKEN com pelo menos 32 caracteres, idêntico na interface e na API.")
        else:
            item("Autenticação da API", "ok", "Proteção por token ativada. OIDC é configurado na interface.")
    else:
        item("Autenticação da API", "aviso", "API sem autenticação.", "Para habilitar, siga docs/autenticacao.md.")
    if settings.APP_MODE == "presentation":
        item("Alertas", "aviso", "Modo apresentação: webhook externo desabilitado, mesmo se configurado. Alertas apenas em log.")
    else:
        item("Alertas", "nao_verificado" if settings.WEBHOOK_URL else "aviso", "Webhook preenchido; entrega não testada." if settings.WEBHOOK_URL else "Somente log; nenhuma entrega externa de alertas.")
    return {"verificado_em": datetime.now(timezone.utc).isoformat(), "apresentacao": {"ativa": settings.APP_MODE == "presentation", "llm_real": settings.PRESENTATION_USE_LLM}, "itens": itens}
