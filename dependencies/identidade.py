from fastapi import Header, HTTPException, Depends
from repositories.identidade_externa_repository import buscar_usuario_id_por_identidade
from typing import Annotated
import secrets
from os import getenv
from dotenv import load_dotenv
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from dependencies.autenticacao_servico import bearer
from models.financas import Usuario
from services.auth_service import decodificar_token

load_dotenv()

def obter_usuario_id_atual(
        credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
        provedor: str | None = Header(default=None, alias = 'X-Identity-Provider'), 
        identificador_externo: str | None=Header(default=None, alias='X-External-Identity'),
        db: Session = Depends(get_db)) -> int:

    if not credenciais or not credenciais.scheme.upper() == "BEARER":
        raise HTTPException(status_code=401, detail="Não autenticado")


    key = getenv("INTERNAL_API_KEY")

    if key and secrets.compare_digest(credenciais.credentials, key):
        if not provedor or not identificador_externo:
            raise HTTPException(status_code=403, detail="identidade não autorizada")
        usuario_id = buscar_usuario_id_por_identidade(provedor, identificador_externo)
        if not usuario_id:
            raise HTTPException(status_code=403, detail="identidade não autorizada")
        return usuario_id

    try:
        usuario_id = decodificar_token(credenciais.credentials, tipo_esperado="access")
    except ValueError as erro:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado") from erro

    usuario = (
        db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.ativo.is_(True)).first()
    )

    if not usuario:
        raise HTTPException(status_code=403, detail='Usuário desativo ou não encontrado')

    return usuario.id