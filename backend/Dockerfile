# Imagem base leve
FROM python:3.12-slim

# Dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala uv (binário oficial)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Diretório da aplicação
WORKDIR /app

# Copia apenas arquivos de dependência primeiro (cache de build)
COPY pyproject.toml uv.lock ./

# Cria venv + instala deps
RUN uv sync --frozen --no-cache --no-install-project

# Copia código da aplicação
COPY . .

# Instala só o projeto local (rápido)
RUN uv sync --frozen --no-cache

# Permissão de execução para scripts
RUN chmod +x start.sh

# Porta informativa
EXPOSE 80

# Executa via script
CMD ["/bin/bash", "start.sh"]