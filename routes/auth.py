from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta

from models.chat import MensagemChat
from models.financas import Financa, IdentidadeExterna, Usuario
from schemas.auth import (
    RequestEsqueciSenha,
    RequestGoogleAuth,
    RequestLogin,
    RequestRedefinirSenha,
    RequestRefresh,
    RequestRegistro,
    ResponseTokens,
    ResponseUsuarioAuth
)
from database import get_db
from repositories.integracao_usuario_repository import buscar_integracao_principal, selecionar_integracao_principal
from services.auth_service import criar_access_token, criar_refresh_token, gerar_hash_senha, verificar_senha, validar_token_google, decodificar_token, enviar_email_recuperacao
from dependencies.identidade import obter_usuario_id_atual

auth_router = APIRouter(prefix="/auth", tags=["auth"])

def montar_resposta_tokens(usuario: Usuario) -> ResponseTokens:
    provedor_principal = buscar_integracao_principal(usuario.id)

    return ResponseTokens(
        access_token = criar_access_token(usuario.id),
        refresh_token = criar_refresh_token(usuario.id),
        usuario = ResponseUsuarioAuth(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            saldo=usuario.saldo,
            provedor_principal=provedor_principal,
        ),
    )

@auth_router.post("/registro", response_model=ResponseTokens, status_code=201)
async def registrar(dados: RequestRegistro, db: Session = Depends(get_db)):
    email = dados.email.lower().strip()
    nome = dados.nome.strip()

    usuario = db.query(Usuario).filter(Usuario.email==email).first()

    if usuario:
        raise HTTPException(status_code=409, detail="Este usuário já está cadastrado")

    novo_usuario = Usuario(
        nome = nome,
        email = email,
        senha_hash = gerar_hash_senha(dados.senha),
        ativo = True,
        saldo = 0.0,
        proximo_numero_transacao = 1,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    selecionar_integracao_principal(novo_usuario.id, "local")

    return montar_resposta_tokens(novo_usuario)


@auth_router.post("/login", response_model=ResponseTokens)
async def login(dados: RequestLogin, db: Session = Depends(get_db)):
    email = dados.email.lower().strip()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario or not usuario.senha_hash or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorreto")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")

    return montar_resposta_tokens(usuario)

@auth_router.post("/google", response_model=ResponseTokens)
async def login_google(dados: RequestGoogleAuth, db: Session = Depends(get_db)):
    try:
        dados_google = validar_token_google(dados.id_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Valor incorreto")
    except RuntimeError:
        raise HTTPException(status_code=503, detail="RuntimeError")


    identidade = (
        db.query(IdentidadeExterna).filter(
            IdentidadeExterna.identificador_externo == dados_google ["sub"],
            IdentidadeExterna.provedor =="google"
        ).first()
    )

    if identidade:
        usuario = db.query(Usuario).filter(Usuario.id == identidade.usuario_id).first()
    else:
        usuario = db.query(Usuario).filter(Usuario.email==dados_google["email"]).first()

        if usuario:
            nova_identidade = IdentidadeExterna(
                usuario_id = usuario.id,
                provedor = "google",
                identificador_externo = dados_google["sub"]
            )
            db.add(nova_identidade)
            db.commit()
            db.refresh(nova_identidade)

        else:

            usuario = Usuario(
                nome = dados_google["nome"],
                email = dados_google["email"],
                senha_hash = None,
                ativo = True,
                saldo = 0.0,
                proximo_numero_transacao = 1,
            )

            db.add(usuario)
            db.flush()

            nova_identidade = IdentidadeExterna(
                usuario_id = usuario.id,
                provedor = "google",
                identificador_externo = dados_google["sub"]
            )

            db.add(nova_identidade)
            db.commit()
            db.refresh(nova_identidade)
            
        db.refresh(usuario)
        selecionar_integracao_principal(usuario.id, "local")
        
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")

    return montar_resposta_tokens(usuario)

@auth_router.post("/refresh", response_model=ResponseTokens)
async def refresh(dados: RequestRefresh, db: Session = Depends(get_db)):
    try:
        usuario_id = decodificar_token(dados.refresh_token, tipo_esperado="refresh")
    except ValueError:
        raise HTTPException(status_code=401, detail="Tipo diferente do esperado")

    usuario = db.query(Usuario).filter(Usuario.ativo.is_(True), Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=403, detail="Usuário desativado")

    return montar_resposta_tokens(usuario)

@auth_router.get("/me", response_model=ResponseUsuarioAuth)
async def me(usuario_id: int = Depends(obter_usuario_id_atual), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return ResponseUsuarioAuth(
        id = usuario.id,
        nome = usuario.nome,
        email = usuario.email,
        saldo = usuario.saldo,
        provedor_principal= buscar_integracao_principal(usuario.id)
    )   

@auth_router.post("/esqueci-senha")
async def esqueci_senha(dados: RequestEsqueciSenha, db: Session = Depends(get_db)):
    email = dados.email.lower().strip()
    usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo.is_(True)).first()

    if usuario:
        codigo = f"{secrets.randbelow(900000) + 100000}"
        usuario.codigo_recuperacao = codigo
        usuario.codigo_recuperacao_expira_em = datetime.now() + timedelta(minutes=15)
        db.commit()
        enviar_email_recuperacao(email, codigo)

    return {"mensagem": "Se o email estiver cadastrado, enviamos um código de 6 digitos"}

@auth_router.post("/redefinir-senha")
async def redefinri_senha(dados: RequestRedefinirSenha, db: Session = Depends(get_db)):
    email = dados.email.lower().strip()
    usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo.is_(True)).first()

    if (
            not usuario
            or not usuario.codigo_recuperacao
            or usuario.codigo_recuperacao != dados.codigo.strip()
            or not usuario.codigo_recuperacao_expira_em
            or usuario.codigo_recuperacao_expira_em < datetime.now()
        ):
            raise HTTPException(status_code=400, detail="Código inválido ou expirado")
    
    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    usuario.codigo_recuperacao = None
    usuario.codigo_recuperacao_expira_em = None
    db.commit()
    return {"mensagem": "Senha redefinida com sucesso"}

@auth_router.delete("/me")
async def excluir_minha_conta(usuario_id: int = Depends(obter_usuario_id_atual), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db.query(MensagemChat).filter(MensagemChat.usuario_id == usuario_id).delete()
    db.query(Financa).filter(Financa.usuario_id == usuario_id).delete()
    db.query(IdentidadeExterna).filter(IdentidadeExterna.usuario_id == usuario_id).delete()

    usuario.ativo = False
    usuario.nome = "Conta Excluída"
    usuario.email = f"excluido_{usuario.id}@anonimo.local"
    usuario.senha_hash = None
    usuario.saldo = 0.0
    usuario.codigo_recuperacao = None
    usuario.codigo_recuperacao_expira_em = None

    db.commit()
    return{"mensagem": "Conta excluída com sucesso"}
    


