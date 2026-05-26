from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes
)
from os import getenv
from dotenv import load_dotenv
import httpx
import os 

load_dotenv()

TOKEN_TELEGRAM = getenv("TELEGRAM")



app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()

def formatar_mensagem(dados):
    data_formatada = dados.get('data')
    return (
        f"Salvo! \n\n"
        f"Categoria: {dados.get('categoria')}\n"
        f"Valor: {dados.get('valor')}\n"
        f"Descrição: {dados.get('descricao')}\n"
        f"Tipo: {dados.get('tipo')}\n"
        f"Data: {data_formatada}\n"
        
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Olá, pode enviar a mensagem')

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text

    await update.message.reply_text("Processando os dados financeiros...")

    payload = {"texto": mensagem}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post('http://localhost:8000/financas', json=payload)
        
        if response.status_code == 200:
            dados = response.json()
            mensagem_sucesso = formatar_mensagem(dados)
            await update.message.reply_text(mensagem_sucesso)
        
        else:
            await update.message.reply_text("Erro ao salvar no banco")
    
    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")

async def responder_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    audio = await update.message.voice.get_file()

    caminho = "audio_temp.ogg"

    await audio.download_to_drive(caminho)

    with open (caminho, 'rb') as f:
        files ={'file': (caminho, f)}
        async with httpx.AsyncClient() as client:
            response = await client.post('http://localhost:8000/financas/audio', files=files)
    
    if os.path.exists(caminho):
        os.remove(caminho)
        
    if response.status_code == 200:
        dados = response.json()
        mensagem_sucesso = formatar_mensagem(dados)
        await update.message.reply_text(mensagem_sucesso)
    else:
        await update.message.reply_text("Erro ao salvar no banco")
    


    
async def ver_itens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:8000/financas')

        if response.status_code == 200:
            dados = response.json()
            for dado in dados:
                data = (
                    f"ID: {dado["id"]}"
                    f"Valor: {dado["valor"]}"
                    f"Categoria: {dado["categoria"]}"
                    f"Descrição: {dado["descricao"]}"
                    f"Tipo: {dado["tipo"]}"
                    f"Data: {dado["data"]}"
                )
                await update.message.reply_text(data)
        else:
            await update.message.reply_text(f"Erro da API: {response.text}")

    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")

async def atualizar_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    novo_saldo = update.message.text.replace('/atualizar_saldo ', '').strip()

    await update.message.reply_text("Atualizando o saldo...")

    {"Novo saldo": novo_saldo}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put('http://localhost:8000/saldo', json={"saldo": float(novo_saldo)})
        
        if response.status_code == 200:
            saldo = response.json()

            mensagem_sucesso = (
                f"Saldo atualizado com sucesso!\n\n"
                f"Seu saldo é de {saldo}")
            
            await update.message.reply_text(mensagem_sucesso)

        else:
            await update.message.reply_text("Erro ao atualizar o saldo")
    
    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")
                

async def ver_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:8000/saldo')

        if response.status_code == 200:
            dados = response.json()
            for dado in dados:
                data = (
                    f"Seu saldo é de: {dado["saldo"]}"
                )
                await update.message.reply_text(data)
        else:
            await update.message.reply_text(f"Erro da API: {response.text}")

    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")
                


app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), responder))
app.add_handler(CommandHandler("ver_itens", ver_itens))
app.add_handler(CommandHandler("atualizar_saldo", atualizar_saldo))
app.add_handler(CommandHandler("ver_saldo", ver_saldo))
app.add_handler(MessageHandler(filters.VOICE, responder_audio))



if __name__ == '__main__':
    app.run_polling()





