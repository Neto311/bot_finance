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

            campos_obrigatorios = ['access_token', 'refresh_token', 'token_type', 'expires_in']

            for item in campos_obrigatorios:
                if item not in dados:
                    return {'erro': f'faltando o campo {item}'}

            registro_salvo = salvar_tokens(
                usuario = 'usuario_local',
                access_token= dados.get('access_token'),
                refresh_token= dados.get('refresh_token'),
                token_type=dados.get('token_type'),
                expires_in=dados.get('expires_in')
            )

            tokens_oauth['usuario_local'] = {
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
        tokens = buscar_tokens('usuario_local')

        if tokens:
            tokens_oauth['usuario_local'] = tokens

        if not tokens:
            return {'conectado': False}
    return {
        'conectado': True,
        'access_token_presente': bool(tokens.get('access_token')),
        'refresh_token_presente': bool(tokens.get('refresh_token')),
        'token_type': tokens.get('token_type'),
        'expires_at': tokens.get('expires_at')
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

    async with httpx.AsyncClient() as client:
        resultado_sessao = await inicializar_sessao_mcp(client, headers)

        if resultado_sessao.get('erro'):
            return resultado_sessao

        headers_sessao = resultado_sessao.get('headers_sessao')

        if not headers_sessao:
            return{'erro': 'sem headers da sessão'}

        mensagem_ferramentas = {
            'jsonrpc': "2.0",
            'id': 2,
            'method': 'tools/list',
            'params': {}
        }

        response_ferramentas = await client.post('https://mcp.minhaseconomias.com.br/mcp', headers=headers_sessao, json=mensagem_ferramentas)

        evento = extrair_evento_sse(response_ferramentas.text)

        if not evento:
            return {'erro': 'mcp não retornou'}

        resultado = evento.get('result', {})
        ferramentas = resultado.get('tools', [])

        nomes = [ferramenta.get('name') for ferramenta in ferramentas]
        me_= [nome for nome in nomes if nome and nome.startswith("ME_")]

        #chamada get

        evento_categoria = await chamar_ferramenta_mcp (3, 'ME_CategoriasDeTransacao', {'typeTransaction': 'GASTO'}, headers_sessao, client)

        if not evento_categoria:
            return {'erro': 'cliente mcp não enviou resposta'}

        if evento_categoria.get('erro'):
            return evento_categoria

        dados_categorias = extrair_dados_resultado_mcp(evento_categoria)

        if isinstance(dados_categorias, dict) and dados_categorias.get('erro'):
            return dados_categorias
    
        if not dados_categorias:
            primeiro_item = None
            chaves_primeiro_item = []
        else:
            primeiro_item = dados_categorias[0]

            if isinstance(primeiro_item, dict):
                chaves_primeiro_item = list(primeiro_item.keys())
            else:
                chaves_primeiro_item = []

        categorias_resumidas = []

        transporte = None

        for categoria in dados_categorias:
            if not isinstance(categoria, dict):
                continue
            categorias_resumidas.append(
                {
                    'nome': categoria.get('categoryName'),
                    'referencia': categoria.get('categoryRef'),
                    'isInternal': categoria.get('isInternal'),
                    'qtd_subcategorias': len(categoria.get('subCategories') or [])

                }
            )

            if categoria.get('categoryName') == 'Transporte':
                transporte = categoria
                break

        if not transporte:
            return {'erro': 'Categoria Transporte não encontrada'}

        subcategorias = transporte.get('subCategories') or []

        primeira_subcategoria = (
            subcategorias[0]
            if subcategorias
            else None
        )

        if isinstance (primeira_subcategoria, dict):
            chaves_subcategoria = list(primeira_subcategoria.keys())
        else:
            chaves_subcategoria = []


        subcategorias_resumidas = []

        combustivel = None

        for subcategoria in subcategorias:
            if not isinstance(subcategoria, dict):
                continue
            subcategorias_resumidas.append({
                'nome': subcategoria.get('subCategoryName'),
                'referencia': subcategoria.get('subCategoryRef'),
                'referencia_categoria': subcategoria.get('categoryRef'),
                'editavel': subcategoria.get('isEditable')
            })

            if subcategoria.get('subCategoryName') == 'Combustível':
                combustivel = subcategoria
                break



        evento_saldo = await chamar_ferramenta_mcp(4, 'ME_Saldo', {}, headers_sessao, client)

        if not evento_saldo:
            return {'erro': 'evento_saldo vazio'}
        
        if evento_saldo.get('erro'):
            return evento_saldo
        
        dados_saldo = extrair_dados_resultado_mcp(evento_saldo)

        if dados_saldo.get('erro'):
            return dados_saldo

        bancos = dados_saldo.get('banks') or []

        if isinstance(bancos, list) and bancos:
            primeiro_banco = bancos[0]
        else:
            primeiro_banco = None

        if isinstance(primeiro_banco, dict):
            chaves_primeiro_banco = list(primeiro_banco.keys())
        else:
            chaves_primeiro_banco = []


        contas_resumidas = []

        conta_principal = None
        conta_destino = None

        for conta in bancos:
            if not isinstance(conta, dict):
                continue
            contas_resumidas.append({
                'nome': conta.get('accountName'),
                'referencia': conta.get('accountRef'),
                'tipo': conta.get('accountType'),
                'descricao_tipo': conta.get('accountTypeDescription'),
                'instituicao': conta.get('financialInstitutionName'),
                'principal': conta.get('main'),
                'arquivada': conta.get('archived')
                }
            )

            if conta.get('main') and not conta.get('archived'):
                conta_principal = conta

            if conta.get('accountName') == 'Nubank' and not conta.get('archived'):
                conta_destino = conta


        

        evento_transacoes = await chamar_ferramenta_mcp(5, 'ME_Transacoes', {
            'types': ['GASTO'],
            'statuses': ['CONFIRMED', 'PENDING'],
            'size': 10,
            'sortDirection': 'DESC'
        }, headers_sessao, client)

        if not evento_transacoes:
                    return {'erro': 'evento_transacoes vazio'}
        if evento_transacoes.get('erro'):
            return evento_transacoes

        dados_transacao = extrair_dados_resultado_mcp(evento_transacoes)

        if isinstance(dados_transacao, dict) and dados_transacao.get('erro'):
            return dados_transacao
        
        if not isinstance(dados_transacao, dict):
            return {
                "erro": "Formato inesperado",
                "tipo": type(dados_transacao).__name__,
            }

        transacoes = dados_transacao.get('transactions') or []

        if transacoes:
            primeira_transacao = transacoes[0]
        else:
            primeira_transacao = []

        if isinstance(primeira_transacao, dict):
            chaves_transacao = list(primeira_transacao.keys())


        ferramentas_criar = None

        for ferramenta in ferramentas:
            if isinstance(ferramenta, dict) and ferramenta.get('name') == 'ME_CriarTransacao':
                ferramentas_criar = ferramenta
                break

        if not ferramentas_criar:
            return {'erro': 'ferramentas_criar vazio'}

        input_schema = ferramentas_criar.get('inputSchema') or {}
        propriedades = input_schema.get('properties') or {}
        obrigatorios = input_schema.get('required') or []

        categoria_ref_presente = False

        if transporte:
            categoria_ref_presente = True if transporte.get('categoryRef') else False

        
        sub_categoria_ref_presente = False

        if combustivel:
            sub_categoria_ref_presente = True if combustivel.get('subCategoryRef') else False


        conta_ref_presente = False

        if conta_principal:
            conta_ref_presente = True if conta_principal.get('accountRef') else False

        if not conta_destino:
            return {'erro': 'Conta Nubank não encontrada'}

        argumentos = {
            'categoryRef': transporte.get('categoryRef'),
            'subCategoryRef': combustivel.get('subCategoryRef'),
            'accountRef': conta_destino.get('accountRef'),
            'dateTransaction': date.today().strftime('%Y-%m-%d'),
            'description': 'TESTE BOT MCP - EXCLUIR',
            'typeTransaction': 'GASTO',
            'value': 0.01,
            'isConsolidated': True
        }




    return {
       'conta_destino': bool(conta_destino),
       'nome_conta': conta_destino.get('accountName'),
       'ref': bool(conta_destino.get('accountRef')),
       'arquivada': conta_destino.get('archived')
        }


@me_router.get ('/integracoes/minhas-economias/testar-provider')
async def testar_provider():
    servico = await obter_finance_service('usuario_local')

    if isinstance(servico, dict) and servico.get('erro'):
        return servico

    filtros = {
        'types': ['GASTO'],
        'statuses':['CONFIRMED', 'PENDING'],
        'size': 10,
        'sortDirection': 'DESC'
    }

    dados = await servico.listar_transacoes(filtros)

    if isinstance(dados, dict) and dados.get('erro'):
        return dados

    transacoes = dados.get('transactions') or []

    categorias = await servico.listar_categorias('GASTO')

    if isinstance(categorias, dict) and categorias.get('erro'):
        return categorias

    contas = await servico.listar_contas()

    if isinstance(contas, dict) and contas.get('erro'):
        return contas

    if not isinstance(categorias, list):
        return {'erro': 'formato inesperado de categorias'}

    if not isinstance(contas, list):
        return {'erro': 'formato inesperado de contas'}


    nubank = False

    for conta in contas:
        if isinstance(conta, dict):
            if conta.get('accountName') == 'Nubank' and not conta.get('archived'):
                nubank = True
                break

    categoria_nome = await servico.buscar_categoria('Transporte', 'GASTO')

    if isinstance(categoria_nome, dict) and categoria_nome.get('erro'):
        return categoria_nome

    subcategoria = await servico.buscar_subcategorias('Transporte', 'Combustível', 'GASTO')

    if isinstance(subcategoria, dict) and subcategoria.get('erro'):
        return subcategoria

    conta = await servico.buscar_conta('Nubank')

    if isinstance(conta, dict) and conta.get('erro'):
        return conta

    dados_teste = {
        'valor': 80,
        'categoria': 'Transporte',
        'subcategoria': 'Combustível',
        'descricao': 'Gasolina',
        'conta': 'Nubank',
        'tipo': 'GASTO',
        'data': '2026-08-17'
    }

    preparacao = await servico.preparar_transacao(dados_teste)

    if isinstance(preparacao, dict) and preparacao.get('erro'):
        return preparacao

    transacoes = dados.get('transactions') or []

    cartao_encontrado = None

    for transacao in transacoes:
        if not isinstance(transacao, dict):
            continue
        cartao = transacao.get('creditCard')

        if isinstance(cartao, dict) and cartao is not None:
            cartao_encontrado = cartao
            break

    cartao = await servico.buscar_cartao('Cartão Nubank')

    if isinstance(cartao, dict) and cartao.get('erro'):
        return cartao

    catalogo = await servico.montar_catalogo_categorias('GASTO')

    if isinstance(catalogo, dict) and catalogo.get('erro'):
        return catalogo

    transporte_catalogo = None
    for item in catalogo:
        if item.get('categoria') == 'Transporte':
            transporte_catalogo = item
            break

    if not transporte_catalogo:
        return {'erro': 'catalogo de transporte nao encontrado'}

    subcategoria_transporte = transporte_catalogo.get('subcategorias') or []
    pedagio = 'Pedágio' in subcategoria_transporte

    texto =  "Gastei 30 reais de pedágio hoje"

    dados_ia_teste = extrair_colunas(texto, catalogo)

    if not isinstance(dados_ia_teste, dict):
        return {'erro': 'formato inesperado da Groq'}
        

    return{
        'ia_valor': dados_ia_teste.get('valor'),
        'ia_categoria': dados_ia_teste.get('categoria'),
        'ia_subcategoria': dados_ia_teste.get('subcategoria'),
        'ia_descricao': dados_ia_teste.get('descricao'),
        'ia_tipo': dados_ia_teste.get('tipo'),
        'ia_data': dados_ia_teste.get('data')
    }

@me_router.post('/integracoes/minhas-economias/testar-criacao')
async def testar_criacao():
    tokens = tokens_oauth.get('usuario_local')

    if not tokens:
        return {'conectar': False}

    access_token = tokens.get('access_token')
    token_type = tokens.get('token_type')

    provedor = MinhasEconomiasProvider(access_token, token_type)

    servico = FinanceService(provedor)

    dados_teste = {
        'valor': 0.01,
        'categoria': 'Transporte',
        'subcategoria': 'Combustível',
        'descricao': 'TESTE CARTAO MCP - EXCLUIR',
        'tipo': 'GASTO',
        'data': '2026-08-17'
    }

    resultado = await servico.registrar_transacao(dados_teste)

    if isinstance(resultado, dict) and resultado.get('erro'):
        return resultado

    erro_presente = bool(resultado.get('erro')) if isinstance(resultado, dict) else False

    return {
        'criacao_concluida': bool(resultado),
        'tipo_resultado': type(resultado).__name__,
        'erro_presente': erro_presente
    }
