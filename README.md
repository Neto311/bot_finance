# 💰 App Finanças IA - Assistente Pessoal via Telegram

Este é um assistente financeiro inteligente integrado ao Telegram que utiliza Inteligência Artificial para processar gastos e rendimentos através de texto e áudio. O projeto utiliza o **Groq (Whisper e Llama 3)** para transformar linguagem natural em dados estruturados e gerenciar sua vida financeira de forma simples e eficiente.

## 🚀 Funcionalidades

-   **Processamento de Áudio (STT):** Envie uma mensagem de voz no Telegram e o sistema transcreve e categoriza o gasto automaticamente usando o modelo `whisper-large-v3-turbo` do Groq.
-   **Processamento de Texto (NLP):** Registre despesas enviando frases como "Gastei 50 reais com pizza ontem". A IA (Llama 3) extrai valor, categoria, descrição e data.
-   **Gestão de Saldo:** Controle de saldo atualizado em tempo real.
-   **CRUD Completo:** Possibilidade de listar, atualizar e deletar transações diretamente pelo chat.
-   **Resumos Mensais:** Gere relatórios de gastos totais e detalhamento por categoria de qualquer mês/ano.
-   **Arquitetura Limpa:** Separação total entre a interface do Bot e a inteligência da API (FastAPI).

## 🛠️ Tecnologias Utilizadas

-   **Linguagem:** Python 3.10+
-   **Framework API:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Banco de Dados:** SQLite com [SQLAlchemy ORM](https://www.sqlalchemy.org/)
-   **IA/Processamento:** [Groq Cloud](https://groq.com/) (Whisper para áudio, Llama 3 para extração de dados)
-   **Interface:** [Telegram Bot API](https://core.telegram.org/bots/api) (`python-telegram-bot`)
-   **Comunicação:** `httpx` para requisições assíncronas

## 📋 Pré-requisitos

-   Python instalado
-   Uma conta na [Groq Cloud](https://console.groq.com/) (API Key)
-   Um bot criado no [BotFather](https://t.me/botfather) (Token do Telegram)

## 🔧 Configuração e Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/SEU_USUARIO/app_financas.git
   cd app_financas
   ```

2. **Crie um ambiente virtual e instale as dependências:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # ou
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   Crie um arquivo `.env` na raiz do projeto com:
   ```env
   TELEGRAM=seu_token_do_telegram
   GROQ=sua_api_key_do_groq
   DATABASE_URL=sqlite:///./financas.db
   ```

## 🏃 Como Rodar

1. **Inicie a API (Servidor):**
   ```bash
   uvicorn main:app --reload
   ```

2. **Em outro terminal, inicie o Bot do Telegram:**
   ```bash
   python services/bot_telegram.py
   ```

## 🤖 Comandos do Bot

-   `/start` - Inicia o bot e exibe boas-vindas.
-   `/ver_itens` - Lista todas as transações cadastradas.
-   `/ver_saldo` - Exibe o saldo atual da conta.
-   `/resumo MM AAAA` - Exibe o gasto total e por categoria do mês.
-   `/deletar_transacao ID` - Remove uma transação específica e ajusta o saldo.
-   `/atualizar_transacao ID NOVO_TEXTO` - Corrige uma transação usando IA para reprocessar o novo texto.
-   **Envio de Áudio/Texto:** Basta falar ou digitar o gasto naturalmente.

---
Desenvolvido por [Seu Nome/Osvaldo Celotto]
