from pwdlib import PasswordHash
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import jwt
import httpx

from dotenv import load_dotenv
from os import getenv
from datetime import datetime, timedelta, timezone

load_dotenv()

JWT_SECRET_KEY = getenv("JWT_SECRET_KEY")
GOOGLE_CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
RESEND_API_KEY = getenv("RESEND_API_KEY")
RESEND_FROM = getenv("RESEND_FROM", "FinaceAi <onboarding@resend.dev>")

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


def enviar_email_recuperacao(destinatario: str, codigo: str) -> None:
    if not RESEND_API_KEY:
          print(f"[FinanceAI - MODO DEV] Código para {destinatario}: {codigo}")
          return
    
    resposta = httpx.post(
         "https://api.resend.com/emails",
         headers={
              "Authorization": f"Bearer {RESEND_API_KEY}",
              "Content-Type": "application/json",

         },
         json={
              "from": RESEND_FROM,
              "to": [destinatario],
              "subject": f"{codigo} é o seu código de segurança FinaceAI",
              "html": (
                f"<div style='font-family:sans-serif;padding:24px;background:#04131E;color:#fff;border-radius:12px'>"
                f"<h2 style='margin:0 0 12px'>Finace<span style='color:#F3C75F'>Ai</span></h2>"
                f"<p>Use o código abaixo para redefinir sua senha:</p>"
                f"<div style='font-size:32px;font-weight:800;letter-spacing:6px;color:#1ED760;margin:20px 0'>{codigo}</div>"
                f"<p style='color:#8BA3B8;font-size:13px'>Este código expira em 15 minutos.</p>"
                f"</div>"
            ),
         },
         timeout=10.0,
         
    )

    if resposta.status_code >= 400:
         print(f"[FinaceAi] Erro Resend ({resposta.status_code}): {resposta.text}")
    