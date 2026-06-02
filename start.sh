#!/bin/bash
# start.sh final surgical version
export PORT=${PORT:-8080}

echo "1. Iniciando API (Porta $PORT)..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "2. Aguardando porta $PORT abrir (via Python)..."
# Loop que usa o próprio Python para verificar a porta (mais seguro que 'nc')
while ! python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(('127.0.0.1', $PORT))" 2>/dev/null; do
  sleep 1
done

echo "3. API online. Iniciando Bot Telegram..."
python3 services/bot_telegram.py
