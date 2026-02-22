#!/bin/bash
set -e

echo "▶️ Executando migrações Alembic..."
uv run alembic upgrade head

echo "🚀 Iniciando aplicação FastAPI..."
exec uv run uvicorn main:app --host 0.0.0.0 --port 80