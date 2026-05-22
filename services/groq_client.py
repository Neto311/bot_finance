from groq import Groq
from os import getenv
from dotenv import load_dotenv
import json

load_dotenv()

GROQ = getenv("GROQ")

client = Groq(api_key = GROQ)

PROMPT = (
    "Você é um extrator de dados. Sua resposta deve conter APENAS um JSON puro, "
    "sem explicações. Extraia do texto: 'valor', 'categoria', 'descricao', 'tipo', 'data'."
    "Se a data nao for mencionada, use a data de hoje (formato YYYY-MM-DD)"
    "O tipo deverá obrigatóriamente ser Débito ou Crédito, exatamente com essa escrita"
    "Se não encontrar algum dado, preencha como null."
    "Os tipos podem ser débito ou crédito, caso não seja dito no texto, considera crédito"
    "Você é um extrator de dados financeiros. Extraia: 'valor' (float), 'categoria', 'descricao' e 'data'.\n"
    "Categorias sugeridas: Alimentação, Transporte, Lazer, Saúde, Moradia, Outros.\n"
    "Responda APENAS o JSON puro. Se não encontrar a categoria, use 'Outros'."
    "Você é um extrator de dados financeiros rigoroso. "
    "Extraia EXATAMENTE o valor numérico mencionado no texto.\n"
    "NUNCA invente valores baseados em conhecimento externo. "
    
)


def extrair_colunas(texto_usuario: str):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [
            {'role': 'system', 'content': PROMPT},
            {'role': 'user', 'content': texto_usuario}
        ],
        response_format={ "type": "json_object" }
        )
    
    dados_extraidos = json.loads(completion.choices[0].message.content)

    return dados_extraidos

