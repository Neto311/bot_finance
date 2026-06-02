from telegram import Update, ReplyKeyboardMarkup, ForceReply
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


async def post_init(application):
    await application.bot.set_my_commands(
        [("start", "🏠 Iniciar e ver menu")])
    

app = ApplicationBuilder().token(TOKEN_TELEGRAM).post_init(post_init).build()
            

def formatar_mensagem(dados):
    data_formatada = dados.get('data')
    return (
        f"Salvo! \n\n"
        f"ID: {dados.get('id')}\n"
        f"Categoria: {dados.get('categoria')}\n"
        f"Valor: {dados.get('valor')}\n"
        f"Descrição: {dados.get('descricao')}\n"
        f"Tipo: {dados.get('tipo')}\n"
        f"Data: {data_formatada}\n"
        
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        ['📋 Ver Gastos', '💰 Consultar Saldo'],
        ['📊 Gerar Resumo', '🔍 Buscar por Data'],
        ['🗑️ Deletar Item', '✏️ Editar Item', '💵 Novo Saldo']
        ]

    markup = ReplyKeyboardMarkup(teclado, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text(
        'Olá! Escolha uma opção rápida ou envie um áudio/texto para anotar um gasto:',
        reply_markup=markup
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text

    if mensagem == '🗑️ Deletar Item':
        return await update.message.reply_text(
            'Qual o ID da transação que deseja DELETAR?',
            reply_markup=ForceReply(selective=True))
    
    if mensagem == '✏️ Editar Item':
        return await update.message.reply_text(
            'Qual o ID da transação que deseja EDITAR e o seu TEXTO? (Ex: 12 pizza 50 reais)',
            reply_markup=ForceReply(selective=True))
    
    if mensagem == '💵 Novo Saldo':
        return await update.message.reply_text(
            'Qual o NOVO SALDO?',
            reply_markup=ForceReply(selective=True))


    if mensagem == '📊 Gerar Resumo':
        return await update.message.reply_text(
            'Por favor, digite o MÊS e o ANO para o RESUMO(Ex: 05 2024)',
            reply_markup=ForceReply(selective=True))
    
    if mensagem == '🔍 Buscar por Data':
      return await update.message.reply_text(
            'Por favor, digite o MÊS e o ANO para a BUSCA(Ex: 05 2024)',
            reply_markup=ForceReply(selective=True))
    if mensagem == '📋 Ver Gastos':
        return await ver_itens(update, context)
    elif mensagem == '💰 Consultar Saldo':
        return await ver_saldo(update, context)
    
    if update.message.reply_to_message:
        pergunta = update.message.reply_to_message.text
        if 'MÊS e o ANO' in pergunta:
            if "RESUMO" in pergunta:
                return await resumo(update, context)
            elif "BUSCA" in pergunta:
                return await ver_transacao_data(update, context)
        if 'DELETAR' in pergunta:
            return await deletar_transacao(update, context)
        if 'EDITAR' in pergunta:
            return await atualizar_transacao(update, context)
        if 'NOVO SALDO' in pergunta:
            return await atualizar_saldo(update, context)



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

async def deletar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_transacao = update.message.text.replace('/deletar_transacao ', '').strip()

    await update.message.reply_text("Deletando a transação...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f'http://localhost:8000/financas/{id_transacao}')
        
        if response.status_code == 200:
            mensagem_sucesso = "Transação deletada com sucesso!"
            await update.message.reply_text(mensagem_sucesso)
        else:
            await update.message.reply_text("Erro ao deletar a transação")
    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")

async def atualizar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem_transacao = update.message.text.replace('/atualizar_transacao ', '').strip()

    partes = mensagem_transacao.split(" ", 1)

    if len(partes) < 2:
        await update.message.reply_text("Formato inválido! Use: /atualizar_transacao ID NOVO_TEXTO")
        return 
    
    id_str = partes[0]
    novo_texto = partes[1]

    if not id_str.isdigit():
        await update.message.reply_text("ID inválido! Use apenas números.")
        return
    

    await update.message.reply_text(f"Atualizando a transação {id_str}")
    
    payload = {"texto": novo_texto}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f'http://localhost:8000/financas/{id_str}', json=payload)
        
        if response.status_code == 200:
            dados = response.json()
            mensagem_sucesso = formatar_mensagem(dados)
            await update.message.reply_text(mensagem_sucesso)
        
        else:
            await update.message.reply_text(f"Erro ao salvar no banco {response.status_code}: {response.text}")
    
    except Exception as e:
        await update.message.reply_text(f"Erro: {e}")

async def ver_transacao_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text.replace('/ver_transacao_data ', '').strip()

    partes = mensagem.split(" ")

    if len(partes) < 2:
        await update.message.reply_text("Formato inválido! Use: /ver_transacao_data MÊS ANO")
        return

    mes = partes[0]
    ano = partes[1]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'http://localhost:8000/financas/data?mes={mes}&ano={ano}')
    
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

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text.replace('/resumo ', '').strip()

    partes = mensagem.split(" ")

    if len(partes) < 2:
        await update.message.reply_text("Formato inválido! Use: /resumo MÊS ANO")
        return

    mes = partes[0]
    ano = partes[1]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'http://localhost:8000/resumo?mes={mes}&ano={ano}')

            if response.status_code == 200:
                dados = response.json()

                texto = f'*Resumo de {dados['mes']}/{dados['ano']}*\n\n'
                texto += f'Gasto total: {dados['gasto_total']:.2f}\n\n'
                texto += "*Por categoria:*\n"

                for categoria, valor in dados['categorias'].items():
                    texto += f'- {categoria}: R${valor:.2f}\n'

                await update.message.reply_text(texto, parse_mode='Markdown')
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
app.add_handler(CommandHandler("deletar_transacao", deletar_transacao))
app.add_handler(CommandHandler("atualizar_transacao", atualizar_transacao))
app.add_handler(CommandHandler("ver_transacao_data", ver_transacao_data))
app.add_handler(CommandHandler("resumo", resumo))



if __name__ == '__main__':
    app.run_polling()





