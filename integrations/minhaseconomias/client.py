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
    

