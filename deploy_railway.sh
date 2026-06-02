#!/bin/bash
# deploy_railway.sh
export PORT=${PORT:-8080}

echo "1. Iniciando API (Porta $PORT)..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "2. Aguardando porta $PORT abrir..."
# Loop usando Python para verificar se a API subiu
while ! python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('127.0.0.1', $PORT))" 2>/dev/null; do
  sleep 1
done

echo "3. API online. Aguardando 5s para o Telegram liberar sessões antigas..."
sleep 5

echo "4. Iniciando Bot Telegram..."
python3 services/bot_telegram.py
