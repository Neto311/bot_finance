import secrets
import hashlib
import base64
import json

def gerar_dados_oauth():
    code_verifier = secrets.token_urlsafe(64)
    hash_verifier = hashlib.sha256(code_verifier.encode("ascii")).digest()

    code_challenge = base64.urlsafe_b64encode(hash_verifier).decode("ascii").rstrip("=")

    state = secrets.token_urlsafe(32)

    return {
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "state": state
    }