import asyncio
import logging
import os
import tempfile
from os import getenv
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram import ForceReply, ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)

load_dotenv()

TOKEN_TELEGRAM = getenv("TELEGRAM")
INTERNAL_API_KEY = getenv("INTERNAL_API_KEY")
API_URL = getenv("API_URL", "http://0.0.0.0:10000")
API_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
AUDIO_TIMEOUT = httpx.Timeout(180.0, connect=10.0)

async def post_init(application):
    await application.bot.set_my_commands(
        [("start", "🏠 Iniciar e ver menu")])


app = ApplicationBuilder().token(TOKEN_TELEGRAM).post_init(post_init).build()


def formatar_mensagem(dados):
    data_formatada = dados.get('data')
    return (
        f"Salvo! \n\n"
        f"ID: {dados.get('numero_usuario')}\n"
        f"Categoria: {dados.get('categoria')}\n"
        f"Valor: {dados.get('valor')}\n"
        f"Descrição: {dados.get('descricao')}\n"
        f"Tipo: {dados.get('tipo')}\n"
        f"Data: {data_formatada}\n"

    )

async def montar_headers(update: Update):
    usuario = update.effective_user

    if not usuario:
        if update.message:
            await update.message.reply_text(
                'Erro: usuário não identificado'
            )
        return None

    if not INTERNAL_API_KEY:
        logger.critical("Erro crítico na INTERNAL_API_KEY")
        await update.message.reply_text("Serviço temporariamente indisponível")
        return None

    return{
        'X-Identity-Provider': 'telegram',
        'X-External-Identity': str(usuario.id),
        "Authorization": f"Bearer {INTERNAL_API_KEY}"
    }


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
            'Qual o ID da transação que deseja DELETAR? (Ex: 12)',
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

    usuario_telegram = update.effective_user

    if not usuario_telegram:
        await update.message.reply_text('Erro de identificação')
        return

    payload = {"texto": mensagem, "provedor": "telegram", "identificador_externo": str(usuario_telegram.id)}

    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(f'{API_URL}/financas', json=payload, headers=headers)

        if response.status_code == 200:
            dados = response.json()
            mensagem_sucesso = formatar_mensagem(dados)
            await update.message.reply_text(mensagem_sucesso)

        else:
            await update.message.reply_text("Erro ao salvar no banco")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def responder_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caminho = None

    usuario = update.effective_user

    if not usuario:
        await update.message.reply_text('Usuário não encontrado')
        return

    dados_identidade = {'provedor':'telegram', 'identificador_externo': str(usuario.id)}

    headers = await montar_headers(update)
    
    if not headers:
        return


    try:
        audio = await update.message.voice.get_file()

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as arquivo_temporario:
            caminho = arquivo_temporario.name

        await audio.download_to_drive(caminho)

        conteudo_audio = await asyncio.to_thread(Path(caminho).read_bytes)

        files = {"file": ("audio.ogg", conteudo_audio, "audio/ogg")}

        async with httpx.AsyncClient(timeout=AUDIO_TIMEOUT) as client:
            await update.message.reply_text('Processando áudio...')
            response = await client.post(f'{API_URL}/financas/audio', files=files, data=dados_identidade, headers=headers)

        if response.status_code == 200:
            dados = response.json()
            mensagem_sucesso = formatar_mensagem(dados)
            await update.message.reply_text(mensagem_sucesso)
        else:
            await update.message.reply_text("Erro ao salvar no banco")

    except Exception:
        logger.exception("Erro ao processar áudio recebido do Telegram")
        await update.message.reply_text(
            "Não consegui processar o áudio. Tente novamente"
        )
    finally:
        if caminho and os.path.exists(caminho):
            os.remove(caminho)




async def ver_itens(update: Update, context: ContextTypes.DEFAULT_TYPE):

    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(f'{API_URL}/financas', headers=headers)

        if response.status_code == 200:
            dados = response.json()
            for dado in dados:
                data = (
                    f"ID: {dado["numero_usuario"]}\n"
                    f"Valor: R$ {float(dado["valor"]):.2f}\n"
                    f"Categoria: {dado["categoria"]}\n"
                    f"Descrição: {dado["descricao"]}\n"
                    f"Tipo: {dado["tipo"]}\n"
                    f"Data: {dado["data"]}"
                )
                await update.message.reply_text(data)
        else:
            await update.message.reply_text(f"Erro da API: {response.text}")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def atualizar_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    novo_saldo = update.message.text.replace('/atualizar_saldo ', '').strip()

    await update.message.reply_text("Atualizando o saldo...")

    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.put(f'{API_URL}/saldo', json={"saldo": float(novo_saldo)}, headers=headers)

        if response.status_code == 200:
            saldo = response.json()

            mensagem_sucesso = (
                f"Saldo atualizado com sucesso!\n\n"
                f"Seu saldo é de {saldo}")

            await update.message.reply_text(mensagem_sucesso)

        else:
            await update.message.reply_text("Erro ao atualizar o saldo")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def ver_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(f'{API_URL}/saldo', headers=headers)

        if response.status_code == 200:
            dados = response.json()
            for dado in dados:
                data = (
                    f"Seu saldo é de: {dado["saldo"]}"
                )
                await update.message.reply_text(data)
        else:
            await update.message.reply_text(f"Erro da API: {response.text}")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def deletar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    codigo_transacao = (update.message.text.replace('/deletar_transacao ', '').strip().upper())

    if not codigo_transacao.isdigit():
        await update.message.reply_text("Código inválido. Informe no formato 12")
        return

    headers = await montar_headers(update)

    numero_usuario = int(codigo_transacao)

    if not headers:
        return

    await update.message.reply_text("Deletando a transação...")

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.delete(f'{API_URL}/financas/{numero_usuario}', headers=headers)

        if response.status_code == 200:
            mensagem_sucesso = "Transação deletada com sucesso!"
            await update.message.reply_text(mensagem_sucesso)
        else:
            await update.message.reply_text(f"Erro {response.status_code}: {response.text}")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def atualizar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem_transacao = update.message.text.replace('/atualizar_transacao ', '').strip()

    partes = mensagem_transacao.split(" ", 1)

    if len(partes) < 2:
        await update.message.reply_text("Formato inválido! Use: /atualizar_transacao ID NOVO_TEXTO")
        return

    numero_usuario_str = partes[0]
    novo_texto = partes[1]

    if not numero_usuario_str.isdigit():
        await update.message.reply_text("ID inválido! Use apenas números.")
        return

    numero_usuario = int(numero_usuario_str)

    await update.message.reply_text(f"Atualizando a transação {numero_usuario}")

    payload = {"texto": novo_texto}

    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.put(f'{API_URL}/financas/{numero_usuario}', json=payload, headers=headers)

        if response.status_code == 200:
            dados = response.json()
            mensagem_sucesso = formatar_mensagem(dados)
            await update.message.reply_text(mensagem_sucesso)

        else:
            await update.message.reply_text(f"Erro ao salvar no banco {response.status_code}: {response.text}")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def ver_transacao_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text.replace('/ver_transacao_data ', '').strip()

    partes = mensagem.split(" ")

    if len(partes) < 2:
        await update.message.reply_text("Formato inválido! Use: /ver_transacao_data MÊS ANO")
        return

    mes = partes[0]
    ano = partes[1]

    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(f'{API_URL}/financas/data?mes={mes}&ano={ano}', headers=headers)

            if response.status_code == 200:
                dados = response.json()
                for dado in dados:
                    data = (
                        f"ID: {dado["numero_usuario"]}"
                        f"Valor: {dado["valor"]}"
                        f"Categoria: {dado["categoria"]}"
                        f"Descrição: {dado["descricao"]}"
                        f"Tipo: {dado["tipo"]}"
                        f"Data: {dado["data"]}"
                    )
                    await update.message.reply_text(data)
            else:
                await update.message.reply_text(f"Erro da API: {response.text}")
    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem = update.message.text.replace('/resumo ', '').strip()

    partes = mensagem.split(" ")

    if len(partes) < 2:
        await update.message.reply_text("Formato inválido! Use: /resumo MÊS ANO")
        return

    mes = partes[0]
    ano = partes[1]

    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(f'{API_URL}/resumo?mes={mes}&ano={ano}', headers=headers)

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
    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def meu_id(update, context):
    usuario = update.effective_user

    if not usuario:
        await update.message.reply_text('Erro: não foi possível identificar usuário')
        return

    texto = f'Seu ID do telegram é: {usuario.id}'

    await update.message.reply_text(texto)

async def conectar_minhas_economias(update: Update, context: ContextTypes.DEFAULT_TYPE,):
    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(f"{API_URL}/integracoes/minhas-economias/conectar", headers=headers)

            if response.status_code == 200:
                dados = response.json()

                url_autorizacao = dados.get("url_autorizacao")

                if not url_autorizacao:
                    await update.message.reply_text("Não foi possível gerar o link de autorização.")
                    return

                botao = InlineKeyboardButton("🔗 Conectar ao Minhas Economias", url=url_autorizacao)
                teclado = InlineKeyboardMarkup([[botao]])
                
                await update.message.reply_text("Toque abaixo para conectar sua conta:", reply_markup=teclado,)

            elif response.status_code == 403:
                await update.message.reply_text("Seu usuário não está autorizado.")
            else:
                await update.message.reply_text(f"Não foi possível iniciar a conexão. Código: {response.status_code}")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")

async def desconectar_minhas_economias(update: Update, context: ContextTypes.DEFAULT_TYPE,):
    headers = await montar_headers(update)

    if not headers:
        return

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.delete(f'{API_URL}/integracoes/minhas-economias/conexao', headers=headers)

        if response.status_code == 200:
            dados = response.json()
            token_removido = dados.get("token_removido")
            if token_removido:
               await update.message.reply_text(" Minhas Economias Desconectado ")
            else: 
                await update.message.reply_text(" Sua conta já estava desconectada ")

        elif response.status_code == 403:
            await update.message.reply_text("Usuário não autorizado")

        else:
            await update.message.reply_text(f"Não foi possível desconectar. Código: {response.status_code}")

    except httpx.TimeoutException:
        await update.message.reply_text("A API demorou para responder.")

    except httpx.RequestError:
        logger.exception("Falha de comunicação com a API")
        await update.message.reply_text("Não foi possível comunicar com a API.")

    except (ValueError, TypeError):
        logger.exception("Dados inválidos recebidos pelo bot")
        await update.message.reply_text("Os dados informados são inválidos.")



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
app.add_handler(CommandHandler("meuid",meu_id))
app.add_handler(CommandHandler("conectar_minhas_economias", conectar_minhas_economias))
app.add_handler(CommandHandler("desconectar_minhas_economias", desconectar_minhas_economias))



if __name__ == '__main__':
    print("🤖 Iniciando Bot do Telegram...")
    app.run_polling()





