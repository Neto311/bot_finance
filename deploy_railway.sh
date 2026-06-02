#!/bin/bash
# deploy_railway.sh - Versão Final Certeira
export PORT=${PORT:-8080}

echo "1. Iniciando API..."
# Rodamos a API em background. O log vai direto para o Railway.
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "2. Aguardando API (Porta $PORT)..."
# Loop Python para garantir que a API abriu a porta
python3 -c "
import socket, time
for i in range(30):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', $PORT))
            print('API Online!')
            break
    except:
        time.sleep(1)
"

echo "3. Iniciando Bot..."
# Iniciamos o bot como processo principal
python3 services/bot_telegram.py
