export PORT=${PORT:-8080}

echo "Iniciando API na porta $PORT..."
nohup uvicorn main:app --host 0.0.0.0 --port $P0RT > api.log 2>&1 &

echo "Aguardando API estabilizar..."
sleep 60

echo "Iniciando Bot Telegram..."
python3 services/bot_telegram.py
