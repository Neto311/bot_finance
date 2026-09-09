from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from services.minhas_economias_oauth import gerar_dados_oauth
from integrations.minhaseconomias.client import extrair_evento_sse, chamar_ferramenta_mcp, extrair_dados_resultado_mcp, inicializar_sessao_mcp
from urllib.parse import urlencode
from os import getenv
from dotenv import load_dotenv
import httpx
import json
from datetime import datetime, date
from providers.minhas_economias_provider import MinhasEconomiasProvider
from services.finance_service import FinanceService
from services.groq_client import extrair_colunas
from integrations.minhaseconomias.auth_store import tokens_oauth, tentativas_oauth
from services.finance_service_factory import obter_finance_service
from repositories.minhas_economias_token_repository import salvar_tokens, buscar_tokens
from services.minhas_economias_token_service import renovar_token

load_dotenv()
CLIENT_ID = getenv("MINHAS_ECONOMIAS_CLIENT_ID")
REDIRECT_URI = getenv("MINHAS_ECONOMIAS_REDIRECT_URI")
USUARIO_MVP_ID = 1

me_router = APIRouter()

@me_router.get('/integracoes/minhas-economias/callback')
async def callback(code: str, state:str ):
    if state not in tentativas_oauth:
        return {'erro': 'Tentativa do oauth expirada ou inválida'}

    tentativa = tentativas_oauth.pop(state)
    code_verifier = tentativa["code_verifier"]
    usuario_id = tentativa.get("usuario_id")

    if not isinstance(usuario_id, int):
        return{'erro': 'usuário OAuth inválido'}

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

            campos_obrigatorios = ['access_token', 'refresh_token', 'token_type', 'expires_in']

            for item in campos_obrigatorios:
                if item not in dados:
                    return {'erro': f'faltando o campo {item}'}

            registro_salvo = salvar_tokens(
                usuario_id = usuario_id,
                access_token= dados.get('access_token'),
                refresh_token= dados.get('refresh_token'),
                token_type=dados.get('token_type'),
                expires_in=dados.get('expires_in')
            )

            tokens_oauth[usuario_id] = {
                'access_token': dados.get('access_token'),
                'refresh_token': dados.get('refresh_token'),
                'expires_at': registro_salvo.expires_at,
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
        "code_verifier": dados_oauth["code_verifier"],
        'usuario_id': USUARIO_MVP_ID
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
    tokens = tokens_oauth.get(USUARIO_MVP_ID)

    if not tokens:
        tokens = buscar_tokens(USUARIO_MVP_ID)

        if tokens:
            tokens_oauth[USUARIO_MVP_ID] = tokens

        if not tokens:
            return {'conectado': False}
    return {
        'conectado': True,
        'access_token_presente': bool(tokens.get('access_token')),
        'refresh_token_presente': bool(tokens.get('refresh_token')),
        'token_type': tokens.get('token_type'),
        'expires_at': tokens.get('expires_at')
    }