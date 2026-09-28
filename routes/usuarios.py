from fastapi import APIRouter, Depends, HTTPException

from dependencies.autenticacao_servico import validar_servico
from dependencies.identidade import obter_usuario_id_atual
from repositories.identidade_externa_repository import obter_ou_criar_usuario
from repositories.integracao_usuario_repository import buscar_integracao_principal
from schemas.usuarios import RequestOnboarding, RequestSelecionarIntegracao
from repositories.minhas_economias_token_repository import buscar_tokens
from repositories.integracao_usuario_repository import selecionar_integracao_principal

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

@usuarios_router.get("/integracao-principal")
def consultar_integracao_principal(usuario_id:int = Depends(obter_usuario_id_atual),):
    provedor = buscar_integracao_principal(usuario_id)
    return {"provedor": provedor}

@usuarios_router.post("/integracao-principal")
def integracao_principal(dados: RequestSelecionarIntegracao, usuario_id: int =Depends(obter_usuario_id_atual)):
    if dados.provedor == 'minhas_economias' and buscar_tokens(usuario_id) is None:
        raise HTTPException(status_code=409, detail="Conecte sua conta ao Minhas Economias antes de selecioná-lo",)

    provedor = selecionar_integracao_principal(usuario_id, dados.provedor)

    return{"provedor": provedor}

