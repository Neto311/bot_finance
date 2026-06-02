#!/bin/bash
# start.sh surgical version
export PORT=${PORT:-8080}

echo "1. Iniciando API (Porta $PORT)..."
# Inicia em background e garante logs limpos
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "2. Aguardando porta $PORT abrir..."
# Loop cirúrgico que espera a porta abrir antes de seguir para o Bot
while ! nc -z localhost $PORT; do   
  sleep 1
done

echo "3. API online. Iniciando Bot Telegram..."
# Bot fica em foreground como processo principal (PID 1)
python3 services/bot_telegram.py
