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
