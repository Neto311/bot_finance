from providers.base import FinanceProvider

class FinanceService:
    def __init__(self, provedor: FinanceProvider):
        self.provedor = provedor 

    async def listar_transacoes(self, filtros):
        return await self.provedor.listar_transacoes(filtros)

    async def criar_transacao(self, dados_transacao):
        return await self.provedor.criar_transacao(dados_transacao)

    async def listar_categorias(self, tipo_transacao):
        return await self.provedor.listar_categorias(tipo_transacao)

    async def listar_contas(self):
        return await self.provedor.listar_contas()

    async def buscar_categoria(self, nome_categoria, tipo_transacao):
        categorias = await self.provedor.listar_categorias(tipo_transacao)

        if isinstance(categorias, dict) and categorias.get('erro'):
            return categorias

        if not isinstance(categorias, list):
            return {'erro': 'formato inesperado'}

        for categoria in categorias:
            nome_recebido = categoria['categoryName']

            if nome_recebido.lower() == nome_categoria.lower():
                return categoria

        return {'erro': 'categoria não encontrada'}

    async def buscar_subcategorias(self, nome_categoria, nome_subcategoria, tipo_transacao):
        categoria = await self.buscar_categoria(nome_categoria, tipo_transacao)

        if categoria.get('erro'):
            return categoria

        subcategorias = categoria['subCategories'] or []

        for subcategoria in subcategorias:
            if subcategoria.get('subCategoryName').lower() == nome_subcategoria.lower():
                return subcategoria

        return {'erro': 'subcategoria não encontrada'}

    async def buscar_conta(self, nome_conta):
        contas = await self.provedor.listar_contas()

        if isinstance(contas, dict) and contas.get('erro'):
            return contas

        if not isinstance(contas, list):
            return {'erro': 'formato inesperado'}

        for conta in contas:
            if not isinstance(conta, dict):
                continue

            nome_recebido = conta.get('accountName')

            if nome_recebido and nome_recebido.lower() == nome_conta.lower() and not conta.get('archived'):
                return conta


        return {'erro': 'conta não encontrada'}

    async def preparar_transacao(self, dados):
        if not isinstance(dados, dict):
            return {'erro': 'dados da transacao inválidos'}

        campos_obrigatorios = ['valor', 'descricao', 'categoria', 'tipo', 'data']

        for campo in campos_obrigatorios:
            if campo not in dados:
                return {'erro': f'o campo {campo} está ausente'}

            if campo == 'valor':
                if dados.get('valor') is None:
                    return {'erro': f'o campo {campo} é nulo'}
            else:
                if not dados.get(campo):
                    return {'erro': f'O campo {campo} é nulo'}

        nome_categoria = dados.get('categoria')
        tipo = dados.get('tipo')

        categoria_encontrada = await self.buscar_categoria(nome_categoria, tipo)

        if categoria_encontrada.get('erro'):
            return categoria_encontrada

        subcategoria_encontrada = None
        nome_subcategoria = dados.get('subcategoria')

        if nome_subcategoria:
            subcategoria_encontrada = await self.buscar_subcategorias(dados.get('categoria'), nome_subcategoria, dados.get('tipo'))

            if subcategoria_encontrada.get('erro'):
                return subcategoria_encontrada

        cartao_encontrado = await self.buscar_cartao('Cartão Nubank')

        if cartao_encontrado.get('erro'):
            return cartao_encontrado

        argumentos_mcp = {
            'categoryRef': categoria_encontrada.get('categoryRef'),
            'creditCardRef': cartao_encontrado.get('creditCardRef'),
            'dateTransaction': dados.get('data'),
            'description': dados.get('descricao'),
            'typeTransaction': dados.get('tipo'),
            'value': dados.get('valor'),
            'isConsolidated': True
        }

        if subcategoria_encontrada:
            argumentos_mcp['subCategoryRef'] = subcategoria_encontrada.get('subCategoryRef')


        return argumentos_mcp

    async def registrar_transacao(self, dados):

        argumentos_mcp = await self.preparar_transacao(dados)

        if not isinstance(argumentos_mcp, dict):
            return {'erro': 'formato inesperado na preparação'}

        if argumentos_mcp.get('erro'):
            return argumentos_mcp
        
        resultado = await self.provedor.criar_transacao(argumentos_mcp)

        if isinstance(resultado, dict) and resultado.get('erro'):
            return resultado

        return resultado

    async def listar_cartoes(self):
        return await self.provedor.listar_cartoes()

    async def buscar_cartao(self, nome_cartao):
        cartoes = await self.listar_cartoes()

        if isinstance(cartoes, dict) and cartoes.get('erro'):
            return cartoes

        if not isinstance(cartoes, list):
            return {'erro': 'formato inesperado de cartões'}

        for cartao in cartoes:
            if not isinstance(cartao, dict):
                continue 

            nome_recebido = cartao.get('name')

            if nome_recebido and nome_recebido.lower() == nome_cartao.lower():
                return cartao

        return {'erro': 'cartão não encontrado'}


    async def montar_catalogo_categorias(self, tipo_transacao):
        categorias = await self.listar_categorias(tipo_transacao)

        if isinstance(categorias, dict) and categorias.get('erro'):
            return categorias
        if not isinstance(categorias, list):
            return {'erro': 'formato inesperado de categorias'}

        catalogo = []

        for categoria in categorias:
            if not isinstance(categoria, dict):
                continue

            nome_categoria = categoria.get('categoryName')

            if not nome_categoria:
                continue

            subcategorias_origem = categoria.get('subCategories') or []
            nomes_subcategorias = []

            if isinstance(subcategorias_origem, list):
                for subcategoria in subcategorias_origem:
                    if not isinstance(subcategoria, dict):
                        continue

                    nomes_subcategoria = subcategoria.get('subCategoryName')

                    if nomes_subcategoria:
                        nomes_subcategorias.append(nomes_subcategoria)

            catalogo.append({
                'categoria': nome_categoria,
                'subcategorias': nomes_subcategorias
                })



        return catalogo