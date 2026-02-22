FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala uv
RUN pip install uv

# Copia arquivos de dependência
COPY pyproject.toml uv.lock ./

# Instala dependências
RUN uv sync --frozen

# Copia código
COPY . .

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]