from integrations.minhaseconomias.auth_store import tokens_oauth
from providers.minhas_economias_provider import MinhasEconomiasProvider
from services.finance_service import FinanceService
from repositories.minhas_economias_token_repository import buscar_tokens
from datetime import datetime, timedelta
from services.minhas_economias_token_service import renovar_token

async def obter_finance_service(usuario):
    tokens = tokens_oauth.get(usuario)

    if not tokens:
        tokens = buscar_tokens(usuario)

        if tokens:
            tokens_oauth[usuario] = tokens

        if not tokens:
            return{'erro': 'minhas economias não conectado'}


    expires_at = tokens.get('expires_at')
    limite_de_seguranca = datetime.now() + timedelta(minutes=2)

    if not expires_at:
        return {'erro': 'expires_at ausente'}

    if expires_at <= limite_de_seguranca:
        resultado = await renovar_token(usuario, tokens.get('refresh_token'))

        if resultado.get('erro'):
            return resultado

        tokens = tokens_oauth.get(usuario)

        if not tokens:
            return {'erro': 'tokens renovados não encontrados no cacho'}

    access_token = tokens.get('access_token')
    token_type = tokens.get('token_type')

    if not access_token or not token_type:
        return {'erro': 'tokens inválidos'}

    provedor = MinhasEconomiasProvider(access_token, token_type)

    servico = FinanceService(provedor)

    return servico