# Login nativo com OpenID Connect

O Streamlit autentica a identidade com `st.login()`, `st.user` e `st.logout()`.
O painel exige e-mail verificado e inclusão em `AUTH_ALLOWED_EMAILS`. Todos os
colaboradores autorizados têm, nesta versão, o mesmo acesso operacional. Não há
cadastro local de senhas, edição de credenciais pela interface ou papel de administrador.

O servidor Streamlit é o intermediário confiável entre o usuário e a API. Uma
credencial de serviço, `MEDIFLOW_API_TOKEN`, protege todos os endpoints da API,
inclusive originais, upload, homologação, Swagger e OpenAPI. Somente `GET /health`
é público. Esse token não é o token Google do usuário e não deve ir ao navegador.
Não existe, nesta etapa, autorização individual por documento ou atribuição de
identidade do auditor nos registros da API. Logout encerra a sessão do painel,
mas não revoga a credencial compartilhada pelos servidores.

## 1. Cadastrar o cliente no Google

No projeto Google Cloud usado pela equipe, configure a tela de consentimento e
crie um cliente OAuth do tipo **Aplicação Web**. Cadastre exatamente:

```text
http://localhost:8501/oauth2callback
```

Para hospedagem, use o domínio HTTPS real com `/oauth2callback` no final, tanto
no provedor quanto no arquivo de secrets. Em projetos com público de teste,
adicione os colaboradores como usuários de teste, quando exigido pelo Google.
A lista do Google não substitui `AUTH_ALLOWED_EMAILS` no MediFlow.

Referências: [Google OIDC](https://developers.google.com/identity/openid-connect/openid-connect)
e [Streamlit: autenticação](https://docs.streamlit.io/develop/concepts/connections/authentication).

## 2. Configurar os arquivos privados

Copie `.streamlit/secrets.example.toml` para `.streamlit/secrets.toml`. Preencha
`client_id` e `client_secret` com o cliente OAuth real e gere `cookie_secret` aleatório.
Esse arquivo já é ignorado pelo Git. Para gerar um segredo no terminal local:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Execute novamente para criar um segredo **diferente** para `MEDIFLOW_API_TOKEN`.
Guarde este segundo valor no `.env`, junto das configurações:

```dotenv
AUTH_ENABLED=true
AUTH_PROVIDER=google
AUTH_ALLOWED_EMAILS=colaborador1@example.com,colaborador2@example.com
MEDIFLOW_API_TOKEN=<segredo-aleatorio-gerado-no-terminal>
```

Use a mesma credencial de serviço na UI e na API. Não reutilize a API key Gemini
como cliente OAuth, cookie de sessão ou token da API. Não envie os segredos ao chat
nem versione os arquivos privados. Mudanças no `.env`, secrets e lista de acesso
devem ser aplicadas reiniciando os serviços. A lista é conferida em cada execução
do painel, mas não cancela requisições que já estiverem em processamento.

## 3. Executar

Na instalação Python local:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn presentation.api.main:app --host 127.0.0.1 --port 8000
# Em outro terminal, na raiz do projeto:
.\.venv\Scripts\python.exe -m streamlit run presentation/web/app.py
```

No Docker com emulador OCI e autenticação:

```powershell
docker compose -f docker-compose.yml -f docker-compose.oci-local.yml -f docker-compose.auth.yml up --build -d
```

A reconstrução da imagem instala o complemento `streamlit[auth]`. O arquivo
`secrets.toml` é montado somente para leitura na UI e não é incorporado à imagem.
A porta da API fica ligada apenas ao localhost; a UI usa a rede interna do Docker.
Em hospedagem, mantenha a API privada e publique a UI por HTTPS. Configure a mesma
política `AUTH_ENABLED=true` nos dois serviços: proteger somente a UI não protege
a API, e proteger somente a API não autentica o usuário.

O endpoint de readiness passa a exigir a credencial de serviço. Para chamadas
administrativas ou scripts, use `Authorization: Bearer <MEDIFLOW_API_TOKEN>`.
Os scripts de validação que instanciam o caso de uso diretamente continuam sendo
ferramentas administrativas locais, não clientes autenticados do Google.

## Desenvolvimento e validação

O padrão `AUTH_ENABLED=false` preserva o desenvolvimento local atual e o painel
identifica esse modo explicitamente. Isso não simula login. Ao ativar, configurações
ausentes ou conta não autorizada bloqueiam o acesso; não há retorno automático ao
modo anônimo.

Os testes locais usam identidades simuladas e verificam autorização, bloqueio dos
endpoints, logout e envio da credencial pelo servidor. A conclusão do OAuth real
precisa ser validada no navegador com o cliente do Google configurado. Não foi
criado cliente OAuth nem feita autenticação externa automaticamente.

Outro provedor OIDC pode ser configurado como `[auth.<nome>]` e selecionado por
`AUTH_PROVIDER`. Ele precisa disponibilizar e-mail verificado (`email_verified=true`);
o formato dos claims deve ser validado antes do uso. A implementação inicial foi
preparada para Google, sem integração genérica com qualquer serviço OAuth 2.0.
