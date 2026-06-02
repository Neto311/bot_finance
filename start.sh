#!/bin/bash
# Inicia a API em segundo plano
# O Render fornece a porta automaticamente na variável $PORT
uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} &

# Inicia o Bot do Telegram
python3 services/bot_telegram.py
