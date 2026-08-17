from providers.base import FinanceProvider
import httpx
from integrations.minhaseconomias.client import inicializar_sessao_mcp, chamar_ferramenta_mcp, extrair_dados_resultado_mcp

class MinhasEconomiasProvider(FinanceProvider):
    def __init__(self, access_token, token_type):
        self.access_token = access_token
        self.token_type = token_type

    def _montar_headers(self):
        return {
            'Authorization': f'{self.token_type} {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }

    async def _executar_ferramenta(self, id_chamada, nome_ferramenta, argumentos):
        headers = self._montar_headers()

        async with httpx.AsyncClient() as client:
            resultado_sessao = await inicializar_sessao_mcp(client,headers)

            if resultado_sessao.get('erro'):
                return resultado_sessao

            headers_sessao = resultado_sessao.get('headers_sessao')

            if not headers_sessao:
                return {'erro': 'sem headers_sessao'}

            evento = await chamar_ferramenta_mcp(
                id_chamada,
                nome_ferramenta,
                argumentos,
                headers_sessao,
                client
            )

            if evento.get('erro'):
                return evento

            dados = extrair_dados_resultado_mcp(evento)

            return dados

    async def listar_transacoes(self, filtros):
        return await self._executar_ferramenta(2, 'ME_Transacoes', filtros)

    async def criar_transacao(self, dados_transacao):
        return await self._executar_ferramenta(2, 'ME_CriarTransacao', dados_transacao)