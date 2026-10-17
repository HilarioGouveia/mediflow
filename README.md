# 🏥 MediFlow — Agente Autônomo para Triagem Clínica

> Sistema inteligente e autônomo para classificação, extração multimodal estruturada e roteamento condicional de documentos clínicos com persistência em nuvem Oracle Cloud Infrastructure (OCI Always Free)[cite: 3, 5].

---

## 📌 Visão Geral do Projeto

O **MediFlow** processa fluxos documentais em saúde (receitas, laudos de exames, guias e atestados), mitigando atrasos operacionais e erros de digitação[cite: 3]. A solução combina **Clean Architecture**, **Hexagonal Architecture (Ports & Adapters)** e **Monólito Modular**, garantindo isolamento total das regras clínicas em relação a modelos de linguagem e provedores de nuvem.

---

## 🏛️ Diagrama do Fluxo de Decisão Condicional (LangGraph)

O fluxo operacional baseia-se num grafo de estados com arestas condicionais (*Conditional Edges*) para tratamento de urgências e contingência humana (*Human-in-the-Loop*):

```mermaid
flowchart TD
    A([📥 Ingestão: PDF, Imagem ou Texto]) --> B[🧩 Extração Multimodal via LLM Adapter]
    B --> C{⚖️ Avaliador Condicional}
    
    C -->|Score < 0.85 ou Dados Ausentes| D[⚠️ Nó de Auditoria Humana]
    C -->|Achado Crítico Detectado| E[🚨 Nó de Emergência Médica]
    C -->|Score >= 0.85 & Consistente| F[📋 Nó de Roteamento Padrão]
    
    D --> G[(☁️ OCI: /auditoria_humana/)]
    D --> H[🖥️ Painel Streamlit Human-in-the-Loop]
    
    E --> I[📢 Alerta Plantão Médico / Webhook]
    E --> J[(☁️ OCI: /processados/urgentes/)]
    
    F --> K[(☁️ OCI: /processados/rotina/)]
    F --> L[🏥 Prontuário / Farmácia / Auditoria]

    G --> M([🏁 Fim])
    J --> M
    K --> M

```

---

## 📂 Estrutura Arquitetural do Repositório

```text
mediflow/
│
├── .env.example                     # Variáveis de ambiente (chaves de API, credenciais OCI)
├── .gitignore
├── README.md                        # Documentação da arquitetura, fluxos e execução
├── pyproject.toml                   # Dependências e metadados do projeto
├── Dockerfile                       # Containerização para deploy na VM OCI Always Free
├── docker-compose.yml               # Execução local da API FastAPI + UI Streamlit
│
├── config/                          # Configurações globais e carregamento de ambiente
│   ├── __init__.py
│   └── settings.py                  # Pydantic Settings (chaves, buckets OCI, thresholds)
│
├── domain/                          # NÚCLEO PURO: Regras clínicas e interfaces (Zero dependências externas)
│   ├── __init__.py
│   ├── entities/                    # Entidades do ecossistema clínico
│   │   ├── __init__.py
│   │   ├── paciente.py              # Identificação e dados demográficos
│   │   ├── documento_clinico.py     # Metadados do documento e hash de integridade
│   │   └── triagem.py               # Resultado do diagnóstico, prioridade e roteamento
│   ├── value_objects/               # Objetos de valor imutáveis
│   │   ├── __init__.py
│   │   ├── prioridade.py            # Enum: Rotina, Prioritário, Urgente
│   │   ├── score_confianca.py       # Validação de score (0.00 a 1.00)
│   │   └── cid.py                   # Validação de código CID-10
│   └── ports/                       # Interfaces abstratas / Portas Hexagonais (Protocol/ABC)
│       ├── __init__.py
│       ├── llm_port.py              # Contrato de extração multimodal e classificação
│       ├── storage_port.py          # Contrato de persistência de objetos e buckets
│       └── notifier_port.py         # Contrato para envio de alertas imediatos
│
├── application/                     # CASOS DE USO: Orquestração e fluxo de triagem
│   ├── __init__.py
│   ├── dtos/                        # Schemas Pydantic de entrada e saída (Contrato do Desafio)
│   │   ├── __init__.py
│   │   ├── input_request.py         # Schema da requisição JSON (documento_id, PDF/Base64/texto)
│   │   └── output_response.py       # Schema oficial com classificacao, dados_extraidos e roteamento
│   ├── workflows/                   # Grafo de decisão condicional (State Machine / LangGraph)
│   │   ├── __init__.py
│   │   ├── state.py                 # Estado do fluxo de triagem clínica
│   │   ├── nodes.py                 # Nós: classificar, extrair, avaliar_confianca, rotear
│   │   └── edges.py                 # Arestas condicionais: urgência vs rotina vs revisão humana
│   └── use_cases/                   # Serviços de aplicação
│       ├── __init__.py
│       ├── processar_triagem.py     # Fluxo principal de ingestão, análise e persistência
│       └── auditar_documento.py     # Resolução de casos com baixa confiança por humanos
│
├── infrastructure/                  # ADAPTADORES: Implementações tecnológicas externas
│   ├── __init__.py
│   ├── adapters/                    # Implementação concreta das Portas da camada de Domínio
│   │   ├── __init__.py
│   │   ├── gemini_llm_adapter.py    # Integração multimodal com Google GenAI SDK (Gemini)
│   │   ├── openai_llm_adapter.py    # Fallback/Alternativa para GPT-4o
│   │   ├── oci_storage_adapter.py   # SDK oci.object_storage (Always Free Buckets)
│   │   └── webhook_notifier.py      # Notificador de plantão médico (Slack/Email/Webhook)
│   └── oci_client/                  # Configuração de autenticação OCI (API Key / Instance Principal)
│       ├── __init__.py
│       └── client_factory.py
│
├── presentation/                    # APRESENTAÇÃO: Exposição de interfaces e endpoints
│   ├── __init__.py
│   ├── api/                         # API REST para ingestão e automações
│   │   ├── __init__.py
│   │   ├── main.py                  # Inicialização da aplicação FastAPI
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── triagem_router.py    # Endpoint POST /triagem
│   │       └── health_router.py     # Endpoint GET /health
│   └── web/                         # Painel de Auditoria Human-in-the-Loop
│       ├── app.py                   # Aplicação Streamlit
│       ├── components/              # Componentes de visualização (exibição de PDF e extração)
│       └── views/
│           ├── fila_urgencias.py    # Visualização de casos urgentes
│           └── auditoria.py         # Aprovação/rejeição com um clique de casos ambíguos
│
└── tests/                           # Suíte de testes automatizados
    ├── conftest.py                  # Mocks de LLM e OCI Object Storage
    ├── unit/                        # Testes das regras de negócio do Domínio
    └── integration/                 # Testes dos 3 cenários obrigatórios (Rotina, Urgência, Ambiguidade)

```

---

## ⚙️ Pré-requisitos e Configuração

### 1. Clonar o Repositório e Configurar Variáveis

```bash
git clone https://github.com/HilarioGouveia/mediflow.git
cd mediflow
cp .env.example .env


```

Edite o ficheiro `.env` com as credenciais necessárias:

```ini
GEMINI_API_KEY="sua_chave_gemini"
GEMINI_MODEL_NAME="gemini-3.5-flash"
OCI_CONFIG_FILE="~/.oci/config"
OCI_CONFIG_PROFILE="DEFAULT"
OCI_NAMESPACE="seu_tenancy_namespace"
OCI_BUCKET_NAME="mediflow-documentos-clinicos"

```

### 2. Execução Rápida via Docker Compose

Para iniciar a API FastAPI (porta 8000) e a UI Streamlit (porta 8501) simultaneamente:

```bash
docker-compose up --build -d

```

---

## 🧪 Demonstração dos 3 Cenários Obrigatórios

Execute o script automatizado para verificar a conformidade dos três cenários avaliados:

```bash
python tests/demonstracao_cenarios.py

```

| Cenário | Entrada | Decisão do Grafo | Destino OCI Always Free |
| --- | --- | --- | --- |
| **1. Rotina**<br> | Receita médica ambulatorial legível.

 | Aprovado automaticamente sem contingência humana.

 | `processados/rotina/`<br> |
| **2. Urgência**<br> | Laudo de imagem com TEP agudo detectado.

 | `Fila_Emergencia_Medica` + Disparo imediato de alerta.

 | `processados/urgentes/`<br> |
| **3. Ambiguidade**<br> | Documento rasurado ou CRM ausente (score < 0.85).

 | `requer_auditoria_humana: true` $\rightarrow$ Fila Streamlit.

 | `auditoria_humana/`<br> |

---

## ☁️ Oracle Cloud Infrastructure (OCI Always Free)

A persistência do MediFlow está alinhada às restrições de custo zero do programa ONE:

* **OCI Object Storage**: Organização lógica de buckets por status (`/recebidos`, `/processados`, `/auditoria_humana`).

* **OCI Compute Instance (Opcional)**: Execução conteinerizada via VM Ampere A1 (ARM) ou AMD Micro da camada Always Free.


## Estado de validacao (17/10/2026)

A homologacao de emergencia
persiste o registro antes de chamar o notificador; a resposta inclui `notificacao_enviada`.
Uma falha de notificacao nao desfaz a homologacao.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m pytest tests/unit
python -m uvicorn presentation.api.main:app --host 127.0.0.1 --port 8000
```

Em outro terminal, com o ambiente virtual ativado:

```powershell
python -m streamlit run presentation/web/app.py
```

Edite `.env` com suas configuracoes. `WEBHOOK_URL` e opcional; sem URL, o notificador
registra o alerta apenas em log. O retorno positivo do notificador nesse modo nao
comprova entrega a uma equipe externa.

O armazenamento agora e escolhido explicitamente por `STORAGE_MODE`: `memory`,
`emulator` ou `oci`. O padrao `memory` perde os dados ao reiniciar e pode retornar
`status_backup="sucesso"` para operacoes simuladas. Esse modo nao comprova
persistencia em nuvem. Com `oci` ou `emulator`, erros nao ativam memoria
silenciosamente. Para OCI real no Docker, as credenciais OCI e a
chave privada precisam ser disponibilizadas por montagem de volume, com caminhos
validos dentro do container; o Compose atual nao configura essa montagem.

A conexao real com Gemini terminou em `ConnectError` nas verificacoes. OCI real e
webhook externo permanecem sem validacao. Os tres cenarios em
`tests/demonstracao_cenarios.py` exigem a API ativa na porta 8000 e configuracao de IA;
execute-os separadamente dos testes unitarios.

### Painel operacional

O painel tem navegacao lateral para Nova triagem, Urgencias, Auditoria, Historico e
Integracoes. A triagem aceita PDF, JPG/PNG, TXT, JSON ou texto colado e preserva o
ultimo resultado na sessao. A auditoria permite conferir o original ao lado dos
campos editaveis. O historico consulta documentos armazenados, com busca por ID ou
paciente e exportacao JSON; nao representa um log imutavel de eventos.

Os indicadores fixos foram removidos. Falhas de consulta aparecem como erro, e o
modo em memoria e identificado. A tela Integracoes informa o modo dos adaptadores;
ela nao executa inferencia, teste de conexao OCI ou envio de alertas. O painel de
urgencias nao informa entrega de notificacao sem comprovacao.

A API inclui `GET /triagem/historico`, `GET /triagem/integracoes` e
`GET /triagem/original?caminho=recebidos/...`. Reinicie a API para carregar as rotas
novas. Instale as dependencias atualizadas com `python -m pip install -r requirements.txt`
para habilitar o visualizador PDF nativo. Sem o complemento PDF, o original continua
disponivel para download. O tema visual fica em `.streamlit/config.toml`.

Os testes em `tests/unit/test_painel.py` cobrem as consultas do painel, recuperacao
do original, paginacao OCI, falhas de consulta e preservacao do resultado ao navegar.

O retorno de `salvar_arquivo` e verificado: se o original nao for salvo,
`status_backup="falha"`, mesmo que o relatorio JSON seja salvo depois.

Nao versione `.env`, ambientes virtuais, credenciais OCI ou chaves privadas.

## OCI local em container

O complemento Compose usa [Floci OCI](https://github.com/floci-io/floci-oci),
emulador de terceiros, na versao fixada `0.5.0`. Usa o SDK `oci` nativo e o mesmo
`OCIStorageAdapter` da nuvem. A fabrica de infraestrutura escolhe o ambiente;
dominio, grafo e casos de uso dependem somente de `StoragePort`. O adaptador de
memoria e separado. O emulador nao valida IAM real, assinaturas ou custos Always Free.

Para subir API, interface e emulador:

```powershell
docker compose -f docker-compose.yml -f docker-compose.oci-local.yml up --build -d
```

Interface: http://localhost:8501. API: http://localhost:8000/docs.
O emulador atende apenas na interface local, porta 4599. O bucket configurado em
`OCI_BUCKET_NAME` e criado automaticamente no ambiente emulado. O namespace e
descoberto pelo SDK. Uma chave RSA ficticia e gerada em memoria para assinar as
requisicoes locais; nenhuma credencial Oracle real e usada. O volume nomeado
`mediflow-oci-data` preserva os documentos; nao use `down -v` se quiser mante-los.
Nao e necessario montar o socket Docker no emulador de Object Storage.
O complemento monta os diretorios de codigo em modo somente leitura, facilitando
o desenvolvimento local. Alteracoes no backend exigem reiniciar a API; mudancas
nas dependencias exigem reconstruir a imagem.

Para usar a API executada no Windows com somente o emulador em Docker:

```powershell
docker compose -f docker-compose.yml -f docker-compose.oci-local.yml up -d oci-emulator
```

Configure no `.env`: `STORAGE_MODE="emulator"` e
`OCI_SERVICE_ENDPOINT="http://localhost:4599"`, e reinicie a API. O complemento
Compose define esses valores para os containers automaticamente, sem alterar `.env`.

Teste de integracao real com o SDK OCI, sem chamadas Gemini:

```powershell
$env:RUN_OCI_EMULATOR_TESTS="1"
.\.venv\Scripts\python.exe -m pytest tests/integration/test_oci_emulator.py
```

O teste cria documentos sinteticos em um bucket de teste, consulta o original e o
historico pela API e homologa a auditoria, verificando gravacao, listagem, leitura,
movimentacao e remocao. Remove apenas os objetos que ele proprio criou.

Para conferir persistencia apos reinicio do container:

```powershell
.\.venv\Scripts\python.exe scripts/validar_oci_local.py gravar
docker compose -f docker-compose.yml -f docker-compose.oci-local.yml restart oci-emulator
.\.venv\Scripts\python.exe scripts/validar_oci_local.py conferir
```

Para a nuvem real, use `STORAGE_MODE="oci"`, configure namespace, bucket e
credenciais Oracle e execute sem o complemento `docker-compose.oci-local.yml`.
O bucket deve existir: a criacao automatica esta restrita ao modo emulado.

## Modelo e validacao Gemini

O modelo e configuravel por `GEMINI_MODEL_NAME` no `.env` (padrao:
`gemini-3.5-flash`). Reinicie a API apos alterar o arquivo, pois o servico e
mantido em cache. A tela Integracoes mostra o modelo configurado.

`GEMINI_TIMEOUT_MS` define o timeout de cada chamada (padrao: 20000 ms).
`GEMINI_MAX_ATTEMPTS` limita o total de tentativas (padrao: 3; maximo: 3).
Falhas temporarias de rede, HTTP 408, 429 e 500/502/503/504 recebem tentativas
com espera exponencial e jitter. Erros 400/401/403/404 e respostas invalidas nao
sao repetidos. O SDK tem sua repeticao interna desativada para evitar multiplicacao
de chamadas. A resposta e revalidada com Pydantic antes do roteamento.

Se a extracao falhar, o retorno JSON inclui `status="erro"` e `erro_extracao`
com codigo e mensagem segura. O documento e encaminhado para auditoria humana;
isso nao representa uma classificacao clinica concluida. Campos clinicos vazios e
score zero sao apenas valores de compatibilidade do contrato, nao uma avaliacao
de prioridade. A aprovacao humana resolve o erro atual e conserva o erro anterior
no registro persistido.

Validacao real com dados sinteticos (faz chamadas a API Gemini e pode consumir cota):

```powershell
.\.venv\Scripts\python.exe scripts/validar_gemini.py
.\.venv\Scripts\python.exe scripts/validar_gemini.py --multimodal
```

O primeiro comando verifica rotina, urgencia e ambiguidade. O segundo inclui PDF
digitalizado e PNG sinteticos legiveis. Esses testes nao comprovam precisao clinica
geral, leitura de manuscritos, persistencia OCI real nem entrega de notificacoes.
Falhas de infraestrutura interrompem o teste com codigo de saida diferente de zero.
