import httpx
from dotenv import load_dotenv
from os import getenv
from repositories.minhas_economias_token_repository import salvar_tokens
from integrations.minhaseconomias.auth_store import tokens_oauth

load_dotenv()

CLIENT_ID = getenv('MINHAS_ECONOMIAS_CLIENT_ID')

async def renovar_token(usuario_id, refresh_token):
    if not refresh_token:
        return {'erro': 'refresh token ausente'}

    dados_da_requisicao = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'refresh_token': refresh_token
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post('https://mcp.minhaseconomias.com.br/oauth/token', data=dados_da_requisicao)

            if response.status_code != 200:
                return {'erro': f'falha ao renovar token\n status_code: {response.status_code}'}

            dados = response.json()

            novo_access_token = dados.get('access_token')
            novo_refresh_token = dados.get('refresh_token') or refresh_token
            token_type = dados.get('token_type') or 'Bearer'
            expires_in = dados.get('expires_in')

            if not novo_access_token:
                return {'erro': 'access token ausente na renovação'}

            if not expires_in:
                return{'erro': 'expires_in ausente na renovação'}

            registro_salvo = salvar_tokens(
                usuario_id, novo_access_token, novo_refresh_token, token_type, expires_in
            )

            tokens_oauth[usuario_id] = {
                'access_token': novo_access_token,
                'refresh_token': novo_refresh_token,
                'token_type': token_type,
                'expires_at': registro_salvo.expires_at
            }


            return{
                'renovado': True,
                'access_token_recebido': bool(novo_access_token),
                'refresh_token_recebido': bool(novo_refresh_token),
                'expires_at': registro_salvo.expires_at
            }
        
    except httpx.TimeoutException:
        return{'erro': 'Timeout'}

    except httpx.RequestError:
        return{'erro': 'RequestError'}

