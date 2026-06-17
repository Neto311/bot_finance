from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from os import getenv
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response
import httpx

load_dotenv()
API_URL = getenv('API_URL')

router = APIRouter()


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

@router.post('/whatsapp')
async def responder(request: Request):
    dados_da_twilio = await request.form()
    mensagem_cliente = dados_da_twilio.get('Body')

    payload = {"texto": mensagem_cliente}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f'{API_URL}/financas', json=payload)

        
        if response.status_code == 200:
            dados = response.json()

            txt = F"Salvo: {formatar_mensagem(dados)}"
        else:
            txt = "Erro ao salvar no banco"
        
    except Exception as e:
        txt = f"Erro: {e}"
    
    twilio_resp = MessagingResponse()
    twilio_resp.message(txt)

    return Response(content=str(twilio_resp), media_type = 'application/xml')