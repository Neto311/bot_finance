import secrets
from os import getenv
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth_service import decodificar_token

bearer = HTTPBearer(auto_error=False)

def validar_servico(credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    KEY = getenv('INTERNAL_API_KEY')

    if not credenciais:
        raise HTTPException(status_code=401)

    if credenciais.scheme.upper() != "BEARER":
        raise HTTPException(status_code=401)

    if KEY and secrets.compare_digest(credenciais.credentials, KEY):
        return
    
    else:
        try:
            servico = decodificar_token(credenciais.credentials, tipo_esperado="access")
            if servico:
                return True
        except ValueError:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")