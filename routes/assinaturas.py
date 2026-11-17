from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies.identidade import obter_usuario_id_atual
from models.financas import Usuario
from services.assinatura_service import (
    LIMITE_MENSAGENS_FREE,
    contar_mensagens_mes,
    usuario_eh_pro,)
from schemas.auth import RequestConcederPro
from datetime import datetime, timedelta
import os
import secrets
from fastapi import Header

assinaturas_router = APIRouter(prefix="/assinatura", tags=["assinatura"])


@assinaturas_router.get("/status")
def obter_status_assinatura(
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    eh_pro = usuario_eh_pro(usuario)
    usadas = contar_mensagens_mes(db, usuario_id)
    return {
        "plano": usuario.plano,
        "status_assinatura": usuario.status_assinatura,
        "eh_pro": eh_pro,
        "mensagens_usadas_mes": usadas,
        "limite_free": LIMITE_MENSAGENS_FREE,
        "assinatura_expira_em": usuario.assinatura_expira_em.isoformat()
        if usuario.assinatura_expira_em
        else None,
    }


@assinaturas_router.post("/admin/conceder-pro")
def conceder_pro_admin(
    dados: RequestConcederPro,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    chave_interna = os.getenv("INTERNAL_API_KEY") or ""
    if not chave_interna or not secrets.compare_digest(x_api_key, chave_interna):
        raise HTTPException(status_code=403, detail="Chave administrativa inválida")
    email = dados.email.lower().strip()
    usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo.is_(True)).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.plano = "pro"
    usuario.status_assinatura = "ativa"
    usuario.assinatura_expira_em = (
        datetime.now() + timedelta(days=dados.dias) if dados.dias else None
    )
    db.commit()
    return {
        "mensagem": f"Plano Pro ativado para {usuario.email}",
        "vitalicio": dados.dias is None,
    }