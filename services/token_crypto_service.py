from os import getenv

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

PREFIXO_TOKEN = 'fernet:v1:'

def obter_fernet():
    chave = getenv("TOKEN_ENCRYPTION_KEY")

    if not chave:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY não configurada")

    return Fernet(chave.encode())

def criptografar_token(token:str) -> str:
    if not token:
        raise ValueError("Token está vazio")

    fernet = obter_fernet()

    token_encode = token.encode()
    token_crypt = fernet.encrypt(token_encode)
    token_decode = token_crypt.decode()
    return PREFIXO_TOKEN + token_decode

def descriptografar_token(token_criptografado: str) -> str:
    if not token_criptografado:
        raise ValueError("Token criptografado está vazio")
    
    if not token_criptografado.startswith(PREFIXO_TOKEN):
        raise ValueError("Token não está no formato criptografado esperado")

    conteudo_criptografado = token_criptografado.removeprefix(PREFIXO_TOKEN)

    fernet = obter_fernet()
    token = conteudo_criptografado.encode()
    token_decrypt = fernet.decrypt(token)
    return token_decrypt.decode()

def token_esta_criptografado(token:str | None) -> bool:
    return bool(token and token.startswith(PREFIXO_TOKEN))

    