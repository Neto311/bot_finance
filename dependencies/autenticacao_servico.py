import secrets
from os import getenv
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)

def validar_servico(credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    KEY = getenv('INTERNAL_API_KEY')

    if not KEY:
        raise HTTPException(status_code=503)
    if not credenciais:
        raise HTTPException(status_code=401)

    if credenciais.scheme.upper() != "BEARER":
        raise HTTPException(status_code=401)

    if not secrets.compare_digest(credenciais.credentials, KEY):
        raise HTTPException(status_code=401) 