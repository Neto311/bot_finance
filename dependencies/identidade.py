from fastapi import Header, HTTPException
from repositories.identidade_externa_repository import buscar_usuario_id_por_identidade


def obter_usuario_id_atual(provedor: str | None = Header(default=None, alias = 'X-Identity-Provider'), identificador_externo: str | None=Header(default=None, alias='X-External-Identity')):

    if not provedor or not identificador_externo:
        raise HTTPException(status_code=403, detail='identidade não autorizada')

    usuario_id = buscar_usuario_id_por_identidade(provedor, identificador_externo)

    if not usuario_id:
        raise HTTPException(status_code=403, detail='identidade não autorizada')

    return usuario_id