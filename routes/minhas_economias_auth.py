from os import getenv
from time import monotonic
from typing import Annotated
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends

from dependencies.autenticacao_servico import validar_servico
from dependencies.identidade import obter_usuario_id_atual
from integrations.minhaseconomias.auth_store import tentativas_oauth, tokens_oauth
from repositories.minhas_economias_token_repository import (
    buscar_tokens,
    excluir_tokens,
    salvar_tokens,
)
from services.minhas_economias_oauth import gerar_dados_oauth

load_dotenv()
CLIENT_ID = getenv("MINHAS_ECONOMIAS_CLIENT_ID")
REDIRECT_URI = getenv("MINHAS_ECONOMIAS_REDIRECT_URI")

me_router = APIRouter()

@me_router.get('/integracoes/minhas-economias/callback')
async def callback(code: str, state:str ):
    if state not in tentativas_oauth:
        return {'erro': 'Tentativa do oauth expirada ou inválida'}

    tentativa = tentativas_oauth.pop(state)
    criado_em = tentativa.get("criado_em")
    code_verifier = tentativa["code_verifier"]
    usuario_id = tentativa.get("usuario_id")

    if not isinstance(criado_em, (int, float)):
        return {'erro': 'tentativa OAuth inválida'}

    if monotonic() - criado_em > 600:
        return {'erro': 'tentativa OAuth expirada'}

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
        response = await client.post('https://mcp.minhaseconomias.com.br/oauth/token', data=data)

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

@me_router.post('/integracoes/minhas-economias/conectar', dependencies=[Depends(validar_servico)])
async def conectar(usuario_id: Annotated[int, Depends(obter_usuario_id_atual)]):
    agora = monotonic()

    states_expirados = [state_existente for state_existente, tentativa in tentativas_oauth.items() if not isinstance(tentativa.get("criado_em"), (int, float)) or agora - tentativa["criado_em"] > 600]

    for state_expirado in states_expirados:
        tentativas_oauth.pop(state_expirado, None)

    dados_oauth = gerar_dados_oauth()

    state = dados_oauth['state']

    tentativas_oauth[state] = {
        "code_verifier": dados_oauth["code_verifier"],
        'usuario_id': usuario_id,
        "criado_em": monotonic()
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

    return {'url_autorizacao': url_autorizacao}


@me_router.get('/integracoes/minhas-economias/status', dependencies=[Depends(validar_servico)])
async def verificacao(usuario_id: Annotated[int, Depends(obter_usuario_id_atual)]):
    tokens = tokens_oauth.get(usuario_id)

    if not tokens:
        tokens = buscar_tokens(usuario_id)

        if tokens:
            tokens_oauth[usuario_id] = tokens

        if not tokens:
            return {'conectado': False}
    return {
        'conectado': True,
        'access_token_presente': bool(tokens.get('access_token')),
        'refresh_token_presente': bool(tokens.get('refresh_token')),
        'token_type': tokens.get('token_type'),
        'expires_at': tokens.get('expires_at')
    }

@me_router.delete('/integracoes/minhas-economias/conexao', dependencies=[Depends(validar_servico)])
async def delete_tokens(usuario_id: Annotated[int, Depends(obter_usuario_id_atual)]):
    removido = excluir_tokens(usuario_id)
    tokens_oauth.pop(usuario_id, None)

    return{'conectado': False, 'token_removido': removido}
