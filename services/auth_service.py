from pwdlib import PasswordHash
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import jwt

from dotenv import load_dotenv
from os import getenv
from datetime import datetime, timedelta, timezone

load_dotenv()

JWT_SECRET_KEY = getenv("JWT_SECRET_KEY")
GOOGLE_CLIENT_ID = getenv("GOOGLE_CLIENT_ID")

password_hash = PasswordHash.recommended()

def gerar_hash_senha(senha: str) -> str:
    return password_hash.hash(senha)

def verificar_senha(senha: str, senha_hash: str) -> bool:
    return password_hash.verify(senha, senha_hash)

def criar_access_token(usuario_id: int)-> str:
    if not JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY não configurada")
    
    payload = {
        "sub": str(usuario_id),
        "tipo": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "iat": datetime.now(timezone.utc)
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def criar_refresh_token(usuario_id: int) -> str:
    if not JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY não configurada")
    
    payload = {
        "sub": str(usuario_id),
        "tipo": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "iat": datetime.now(timezone.utc)
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def decodificar_token(token: str, tipo_esperado: str = "access") -> int:
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY não configurada")

    try:
        payload =  jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError as erro:
        raise ValueError("Toekn inválido ou expirado") from erro
    
    if payload.get("tipo") != tipo_esperado:
        raise ValueError("Tipo de token inválido")

    sub = payload.get("sub")

    if not sub or not str(sub).isdigit():
        raise ValueError("Identifiador de usuário inválido no token")

    return int(sub)

def validar_token_google(token_google: str) -> dict:
    if not GOOGLE_CLIENT_ID:
        raise RuntimeError("GOOGLE_CLIENT_ID não configurado")
    
    info = id_token.verify_oauth2_token(token_google, google_requests.Request(), audience=GOOGLE_CLIENT_ID)

    if not info.get("email") or not info.get("email_verified"):
        raise ValueError("Conta Google sem e-mail verificado")
    
    return {
        "sub": str(info["sub"]),
        "email": str(info["email"]).lower().strip(),
        "nome": str(info.get("name") or "Usuário").strip()
    }


