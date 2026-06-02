export PORT=${PORT:-10000}

echo "Iniciando API na porta $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

echo "Aguardando API estabilizar..."
sleep 5

echo "Iniciando Bot Telegram..."
python3 services/bot_telegram.py
