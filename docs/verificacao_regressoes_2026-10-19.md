# Verificação das correções de triagem — 19/10/2026

## Resultados

- `tests/unit`: **98 passaram**, incluindo 13 casos novos de regressão.
- `tests/integration/test_compose_cenarios.py`: **3 passaram** contra a API
  isolada na porta 8001 e o emulador OCI existente na porta 4599.
- `git diff --check`: sem erros de whitespace.

Os testes unitários usaram `.venv/Scripts/python.exe`. A integração utilizou
`docker-compose.yml`, `docker-compose.oci-local.yml` e `docker-compose.test.yml`,
com a imagem local existente (`up -d --no-build`) e os diretórios de código e testes
montados em modo somente leitura. Para instalação limpa, seguir o comando com
`--build` documentado no README.

## Cobertura verificada

1. Achados críticos preservam o alerta ao plantão quando há CRM ausente, paciente
   ausente, baixa confiança ou inconsistência documental. A revisão permanece
   obrigatória, o relatório é persistido na auditoria e o mesmo registro aparece
   nas consultas de auditoria e urgências.
2. Uploads TXT UTF-8, com ou sem BOM, chegam ao adaptador como texto legível,
   preservando acentos e quebras de linha. O armazenamento mantém os bytes originais.
   Entradas inválidas são rejeitadas sem chamar a extração; texto direto permanece literal.
3. Rotina, urgência e ambiguidade foram exercitadas por HTTP real no Compose,
   com extração simulada. O SDK OCI conferiu originais e relatórios no emulador;
   também foram verificadas as decisões, filas e etapas de acompanhamento.
   Os logs da API registraram o alerta no canal `Alerta_Plantao_Medico`.
   Os objetos gerados pela integração foram removidos pelo próprio teste.

## Limites

Nenhum Gemini ou webhook externo foi chamado. A integração confirma o ambiente
local emulado, sem validar credenciais, IAM ou armazenamento na OCI real.
As regras de identificação de achados críticos existentes foram preservadas;
sua validação clínica continua pendente antes do uso real.
As execuções históricas de 18/10/2026 não foram auditadas nesta verificação.
Houve um aviso de depreciação do FastAPI sobre a constante HTTP 422 já usada pelo projeto.
