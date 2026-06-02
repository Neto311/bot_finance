#!/bin/bash
# deploy_railway.sh - Versão de Estabilidade
export PORT=${PORT:-8080}

echo "1. Iniciando API..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "2. Aguardando API (10s)..."
sleep 10

echo "3. Iniciando Bot..."
python3 services/bot_telegram.py
