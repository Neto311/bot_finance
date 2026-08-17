import json


def extrair_evento_sse(texto_sse):
    for linha in texto_sse.splitlines():
        if linha.startswith('data:'):
            conteudo_json = linha.removeprefix('data:').strip()
            evento = json.loads(conteudo_json)
            return evento
    return None

async def chamar_ferramenta_mcp(id_chamada, nome_ferramenta, argumentos, headers, client):
    mensagem = {
        'jsonrpc': '2.0',
        'id': id_chamada,
        'method': 'tools/call',
        'params': {
            'name': nome_ferramenta,
            'arguments': argumentos
        }
    }
    response = await client.post('https://mcp.minhaseconomias.com.br/mcp', headers=headers, json=mensagem)

    if response.status_code != 200:
        return {'erro': response.status_code}

    evento = extrair_evento_sse(response.text)

    if not evento:
        return {'erro': 'resposta SSE ausente'}

    if 'error' in evento:
        return {'erro': evento.get('error')}

    return evento

def extrair_dados_resultado_mcp(evento):
    if not isinstance(evento, dict):
        return {'erro': 'erro de formato'}

    if evento.get('erro'):
        return {'erro': evento.get('erro')}

    resultado = evento.get('result') or {}

    if resultado.get('isError'):
        return {'erro': 'ferramenta MCP com erro'}

    conteudos = resultado.get('content') or []

    if not conteudos:
        return {'erro': 'conteudo ausente'}

    primeiro_bloco = conteudos[0]

    if not isinstance(primeiro_bloco, dict):
        return {'erro': 'bloco inválido'}

    texto = primeiro_bloco.get('text')

    if not texto: 
        return {'erro': 'texto ausente'}

    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        return{'erro': 'texto da ferramenta não é JSON válido'}

    return dados 
    

async def inicializar_sessao_mcp(client, headers):
    initialize = {
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

    response = await client.post('https://mcp.minhaseconomias.com.br/mcp', headers = headers, json=initialize)

    if response.status_code == 200:
        session_id = response.headers.get('mcp-session-id')
        
        if not session_id:
            return {'erro': 'servidor não criou sessão mcp'}
            
        
        notificacao = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }

        headers_sessao = headers.copy()

        headers_sessao['Mcp-Session-Id'] = session_id
    else:
        return {'erro': 'falha ao inciialiar sessão MCP'}

    response_notificacao = await client.post('https://mcp.minhaseconomias.com.br/mcp', headers = headers_sessao, json = notificacao)

    if response_notificacao.status_code != 202:
        return {'erro': response_notificacao.status_code}


    return {
        'headers_sessao': headers_sessao,
        'session_id_presente': bool(session_id)
    }

