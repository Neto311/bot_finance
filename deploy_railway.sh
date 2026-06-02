#!/bin/bash
# deploy_railway.sh - Versão Estabilizada
export PORT=${PORT:-8080}

echo "1. Iniciando API..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "2. Aguardando API estabilizar..."
# Espera a porta abrir
python3 -c "
import socket, time
for i in range(30):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', $PORT))
            break
    except:
        time.sleep(1)
"

echo "3. API Online. Aguardando 30s para evitar conflito de Bot..."
# Esse tempo maior garante que o Railway mate o bot antigo antes do novo tentar ligar
sleep 30

echo "4. Iniciando Bot..."
python3 services/bot_telegram.py
