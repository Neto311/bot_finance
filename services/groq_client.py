from groq import Groq
from os import getenv
from dotenv import load_dotenv
import json
from datetime import date

load_dotenv()

GROQ = getenv("GROQ")

client = Groq(api_key = GROQ)

PROMPT = ("""Você é um extrator de dados financeiros.

Responda APENAS com um objeto JSON válido, sem Markdown e sem explicações.

Extraia exatamente estes campos:
- valor: número
- categoria: texto
- subcategoria: texto ou null
- descricao: texto
- tipo: GASTO ou GANHO
- data: data no formato YYYY-MM-DD

Regras para tipo:
- Gastei, paguei, comprei, débito e despesa significam GASTO.
- Recebi, ganhei, salário, depósito e receita significam GANHO.
- Nunca use Débito ou Crédito no campo tipo.
- O tipo deve ser somente GASTO ou GANHO.

Regras de categoria:
- Gasolina, combustível e posto: categoria Transporte e subcategoria Combustível.
- Restaurante, lanche e refeição: categoria Alimentação.
- Se não identificar uma subcategoria, use null.
- Não invente categorias ou subcategorias.

Regras gerais:
- Extraia exatamente o valor mencionado.
- Nunca invente valores.
- Se a descrição não estiver clara, produza uma descrição curta baseada no texto.
- Se algum dado não puder ser identificado, use null.

Regras de data:
- A data atual será informada junto da mensagem do usuário.
- Se o usuário disser "hoje" ou não informar uma data, use a data atual informada.
- Nunca invente outra data.

Regras do catálogo:
- Quando o catálogo tiver opções, escolha categoria e subcategoria exclusivamente nele.
- Copie os nomes exatamente como aparecem no catálogo.
- A subcategoria escolhida deve pertencer à categoria escolhida.
- Se nenhuma subcategoria se encaixar, use null.
- Quando o catálogo estiver vazio, faça a melhor classificação possível.
"""
)

PROMPT_CHAT = """Você é o roteador inteligente de um assistente financeiro pessoal.

Responda APENAS com um objeto JSON válido, sem Markdown e sem explicações.

Extraia exatamente estes campos:
- intencao: texto (uma das opções abaixo)
- mes: número inteiro de 1 a 12 ou null
- ano: número inteiro de 4 dígitos ou null
- valor: número ou null
- resposta_curta: texto ou null

Opções válidas para o campo intencao:
- REGISTRAR_GASTO: quando o usuário relata uma despesa, compra ou pagamento com valor (ex: "almoço 35", "gastei 50 no uber", "mercado 120 reais").
- CONSULTAR_SALDO: quando o usuário pergunta qual é o saldo atual (ex: "qual meu saldo?", "quanto tenho na conta?", "ver saldo").
- ATUALIZAR_SALDO: quando o usuário quer definir ou alterar o valor do saldo (ex: "meu novo saldo é 2500", "atualizar saldo para 1200").
- RESUMO_MES: quando o usuário pede o resumo, total gasto ou gastos por categoria de um mês (ex: "resumo do mês", "quanto gastei em maio?", "gerar resumo 10 2026").
- LISTAR_RECENTES: quando o usuário pede para ver os últimos gastos ou lançamentos recentes sem especificar um mês fechado (ex: "ver gastos", "últimas transações", "o que gastei recentemente?").
- LISTAR_MES: quando o usuário pede a lista ou extrato de transações de um mês específico (ex: "buscar gastos de agosto", "transações de 05 2026", "extrato desse mês").
- AJUDA: quando o usuário apenas cumprimenta ("oi", "bom dia"), pede ajuda de como usar o app ou envia algo fora do contexto financeiro.

Regras para mes e ano:
- A data atual (YYYY-MM-DD) será informada junto da mensagem.
- Quando a intenção for RESUMO_MES ou LISTAR_MES e o usuário disser "este mês", "mês atual" ou não especificar mês/ano, use o mês e o ano da data atual.
- Se o usuário mencionar apenas o mês (ex: "outubro"), use o ano da data atual.
- Para outras intenções, use null em mes e ano.

Regras para valor:
- Quando a intenção for ATUALIZAR_SALDO, extraia o novo valor numérico do saldo.
- Caso contrário, use null.

Regras para resposta_curta:
- Quando a intenção for AJUDA, escreva uma resposta curta, simpática e direta em português explicando que o usuário pode digitar ou gravar áudio de um gasto (ex: "Uber 25 reais"), consultar saldo, pedir o resumo do mês ou listar os últimos gastos.
- Para todas as outras intenções, use null.
"""

def extrair_colunas(texto_usuario: str, catalogo_categorias=None):

    catalogo = json.dumps([], ensure_ascii=False)

    data_atual = date.today().isoformat()

    if isinstance(catalogo_categorias, list):
        catalogo = json.dumps(catalogo_categorias, ensure_ascii=False)

    mensagem_usuario = f"Data atual: {data_atual}\n Texto do usuário: {texto_usuario} \n Categorias disponíveis: {catalogo}"
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages = [
            {'role': 'system', 'content': PROMPT},
            {'role': 'user', 'content': mensagem_usuario}
        ],
        response_format={ "type": "json_object" }
        )
    
    dados_extraidos = json.loads(completion.choices[0].message.content)

    return dados_extraidos


def extrair_audio(filename):
    with open (filename, 'rb') as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            response_format = "text"
        )

    return transcription

def interpretar_mensagem_chat(texto_usuario:str):
    mensagem_usuario = f"Data atual: {date.today().isoformat()}\n Mensagem Usuário: {texto_usuario}"

    completion = client.chat.completions.create(
        model = "openai/gpt-oss-120b",
        messages = [
                    {'role': 'system', 'content': PROMPT_CHAT},
                    {'role': 'user', 'content': mensagem_usuario}],
        response_format = {"type": "json_object"}
    )

    return json.loads(completion.choices[0].message.content)