from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from services.minhas_economias_oauth import gerar_dados_oauth
from urllib.parse import urlencode
from os import getenv
from dotenv import load_dotenv
import httpx
import json

load_dotenv()
CLIENT_ID = getenv("MINHAS_ECONOMIAS_CLIENT_ID")
REDIRECT_URI = getenv("MINHAS_ECONOMIAS_REDIRECT_URI")

tentativas_oauth = {}
tokens_oauth = {}

me_router = APIRouter()

@me_router.get('/integracoes/minhas-economias/callback')
async def callback(code: str, state:str ):
    if state not in tentativas_oauth:
        return {'erro': 'Tentativa do oauth expirada ou inválida'}

    tentativa = tentativas_oauth.pop(state)
    code_verifier = tentativa["code_verifier"]

    data = {
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID,
                'code': code,
                'code_verifier': code_verifier,
                'redirect_uri': REDIRECT_URI
            }

    async with httpx.AsyncClient() as client:
        response = await client.post(f'https://mcp.minhaseconomias.com.br/oauth/token', data=data)

        if response.status_code == 200:
            dados = response.json()

            tokens_oauth['usuario_local'] = {
                'access_token': dados.get('access_token'),
                'refresh_token': dados.get('refresh_token'),
                'expires_in': dados.get('expires_in'),
                'token_type': dados.get('token_type')

            }
            return {
                'status': 'conexão concluída',
                'access_token_recebido': bool(dados.get("access_token")),
                'refresh_token_recebido': bool(dados.get("refresh_token"))
            }
        else:
            return{
                'status': 'falha na troca do token',
                'http_status': response.status_code
            }
        
@me_router.get('/integracoes/minhas-economias/conectar')
async def conectar():
    dados_oauth = gerar_dados_oauth()

    state = dados_oauth['state']

    tentativas_oauth[state] = {
        "code_verifier": dados_oauth["code_verifier"]
    }

    parametros = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "mcp:read",
        "state": state,
        "code_challenge": dados_oauth["code_challenge"],
        "code_challenge_method": "S256"
    }

    url_autorizacao = (f"https://mcp.minhaseconomias.com.br/oauth/authorize?{urlencode(parametros)}")

    return RedirectResponse(url=url_autorizacao)


@me_router.get('/integracoes/minhas-economias/status')
async def verificacao():
    tokens = tokens_oauth.get("usuario_local")

    if not tokens:
        return {'conectado': False}
    return {
        'conectado': True,
        'access_token_presente': bool(tokens['access_token']),
        'refresh_token_presente': bool(tokens['refresh_token']),
        'token_type': tokens['token_type'],
        'expires_in': tokens['expires_in']
    }

@me_router.get('/integracoes/minhas-economias/testar-mcp')
async def mcp():
    tokens = tokens_oauth.get("usuario_local")

    if not tokens:
        return {'conectado': False}

   
    headers = {
        'Authorization': f"{tokens.get('token_type')} {tokens.get('access_token')}",
        'Content-Type': 'application/json',
        'Accept': "application/json, text/event-stream"
    }

    mensagem ={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "bot-finance",
                "version": "0.1.0"
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://mcp.minhaseconomias.com.br/mcp", headers=headers, json=mensagem)

        session_id = response.headers.get('mcp-session-id')

        if not session_id:
            return {'error': 'servidor não criou sessão mcp'}
        tokens_oauth['usuario_local']['mcp_session_id'] = session_id

        notificacao = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }

        headers['Mcp-Session-Id'] = session_id

        response_notificacao = await client.post("https://mcp.minhaseconomias.com.br/mcp", headers=headers, json=notificacao)

        mensagem_ferramentas = {
            'jsonrpc': "2.0",
            'id': 2,
            'method': 'tools/list',
            'params': {}
        }

        response_ferramentas = await client.post('https://mcp.minhaseconomias.com.br/mcp', headers=headers, json=mensagem_ferramentas)

        texto_sse = response_ferramentas.text

        evento = None

        for linha in texto_sse.splitlines():
            if linha.startswith('data:'):
                conteudo_json = linha.removeprefix('data:').strip()
                evento = json.loads(conteudo_json)
                break

        if evento is None:
            return{'erro': 'nenhum evento mcp encontrado'}

        resultado = evento.get('result', {})
        ferramentas = resultado.get('tools', [])

        nomes = []

        for ferramenta in ferramentas:
            nomes.append(ferramenta.get('name'))

        for nome in nomes:
            if



    return {
        "http_status": response.status_code,
        "notificacao_http_status": response_notificacao.status_code,
        "content_type": response.headers.get('content-type'),
        "sessao_recebida": bool(response.headers.get('mcp-session-id')),

        "ferramentas_http_status": response_ferramentas.status_code,
        "ferramentas_content_type": response_ferramentas.headers.get('content-type') 
    }