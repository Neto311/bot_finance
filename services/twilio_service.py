from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from os import getenv
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response
import httpx

load_dotenv()
API_URL = getenv('API_URL')

router_wpp = APIRouter()


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

@router_wpp.post('/whatsapp')
async def responder_whatsapp(request: Request):
    dados_da_twilio = await request.form()
    mensagem_cliente = dados_da_twilio.get('Body', "").strip()
    comando = mensagem_cliente.lower()

    if not mensagem_cliente:
        return Response(content="<Response></Response>", media_type="application/xml")
    
    async with httpx.AsyncClient() as client:
        if comando == 'listar':
            response = await client.get(f'{API_URL}/financas')
            if response.status_code == 200:
                dados = response.json()
                txt_lista = "*Suas transações*\n\n"

                for i in dados:
                    txt_lista += f"ID: {i['id']} | R$ {i['valor']:.2f} - {i['descricao']}\n"
                
                twilio_resp = MessagingResponse()
                twilio_resp.message(txt_lista)
                return Response(content=str(twilio_resp), media_type="application/xml")
        try:
            payload = {"texto": mensagem_cliente}
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