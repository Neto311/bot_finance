from fastapi import APIRouter, Depends, HTTPException

from dependencies.autenticacao_servico import validar_servico
from repositories.identidade_externa_repository import obter_ou_criar_usuario
from schemas.usuarios import RequestOnboarding

usuarios_router = APIRouter(prefix="/usuarios", dependencies=[Depends(validar_servico)])

@usuarios_router.post("/onboarding")
def onboarding(dados: RequestOnboarding):
    resultado = obter_ou_criar_usuario(
        provedor = dados.provedor,
        identificador_externo= dados.identificador_externo,
        nome=dados.nome
    )

    if resultado["ativo"] is False:
        raise HTTPException(status_code=403, detail="Usuário desativado")
    return resultado 