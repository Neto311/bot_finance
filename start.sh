PORT =${PORT:-10000}

echo "Iniciando API na porta $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT &

sleep 5

echo "Iniciando Bot Telegram..."
python services/bot_telegram.py
