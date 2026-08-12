from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from services.minhas_economias_oauth import gerar_dados_oauth
from urllib.parse import urlencode
from os import getenv
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = getenv("MINHAS_ECONOMIAS_CLIENT_ID")
REDIRECT_URI = getenv("MINHAS_ECONOMIAS_REDIRECT_URI")

tentativas_oauth = {}

me_router = APIRouter()

@me_router.get('/integracoes/minhas-economias/callback')
async def callback():
    return 'status=callbackfuncioando'

@me_router.get('/integracoes/minhas-economias/conectar')
async def conectar():
    dados_oauth = gerar_dados_oauth()

    state = dados_oauth['state']

    tentativas_oauth[state] = {
        "code_verifier": dados_oauth["code_verifier"]
    }

    parametros = {
        "response_typer": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "mcp:read",
        "state": state,
        "code_challenge": dados_oauth["code_challenge"],
        "code_challenge_method": "S256"
    }

    url_autorizacao = (f"https://mcp.minhaseconomias.com.br/oauth/authorize?{urlencode(parametros)}")

    return RedirectResponse(url=url_autorizacao)