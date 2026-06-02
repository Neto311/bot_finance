#!/bin/bash
# deploy_railway.sh - Versão Cirúrgica Final
export PORT=${PORT:-8080}

echo "1. Iniciando API..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "2. Aguardando 60 segundos para o Railway estabilizar e desligar o bot antigo..."
# Aumentamos para 60s para garantir que a versão velha morra antes da nova tentar o token
sleep 60

echo "3. Iniciando Bot..."
python3 services/bot_telegram.py
