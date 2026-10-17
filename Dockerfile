# syntax=docker/dockerfile:1.4

FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependências mínimas de build do SO
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python em prefixo isolado
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------- Final Runtime Stage ----------------

FROM python:3.11-slim AS runtime

WORKDIR /app

# Instalar utilitários de execução
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar bibliotecas instaladas do estágio anterior
COPY --from=builder /install /usr/local

# Copiar código-fonte da aplicação
COPY . .

# Variáveis de ambiente de tempo de execução Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Criar diretório de credenciais da OCI para mapeamento de volume
RUN mkdir -p /root/.oci

# Expor portas para FastAPI (8000) e Streamlit (8501)
EXPOSE 8000 8501

# Comando padrão de inicialização (sobe a API FastAPI)
CMD ["uvicorn", "presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]