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
import stripe
from fastapi import Request

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

@assinaturas_router.post("/checkout")
def criar_checkout_stripe(
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db),
):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    price_id = os.getenv("STRIPE_PRICE_ID")
    app_url = (os.getenv("APP_URL") or "https://app.usefinanceai.com.br").rstrip("/")

    if not stripe.api_key or not price_id:
        raise HTTPException(status_code=503, detail="Pagamento Stripe não configurado")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    params = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "client_reference_id": str(usuario.id),
        "success_url": f"{app_url}/?checkout=sucesso",
        "cancel_url": f"{app_url}/?checkout=cancelado",
        "metadata": {"usuario_id": str(usuario.id)},
    }
    if usuario.gateway_cliente_id:
        params["customer"] = usuario.gateway_cliente_id
    else:
        params["customer_email"] = usuario.email

    sessao = stripe.checkout.Session.create(**params)
    return {"checkout_url": sessao.url}


@assinaturas_router.post("/portal")
def abrir_portal_stripe(
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db),
):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    app_url = (os.getenv("APP_URL") or "https://app.usefinanceai.com.br").rstrip("/")
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario or not usuario.gateway_cliente_id:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura Stripe vinculada")

    sessao = stripe.billing_portal.Session.create(
        customer=usuario.gateway_cliente_id,
        return_url=app_url,
    )
    return {"portal_url": sessao.url}


@assinaturas_router.post("/webhook/stripe")
async def webhook_stripe(request: Request, db: Session = Depends(get_db)):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook Stripe não configurado")

    try:
        evento = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Assinatura do webhook inválida")

    tipo = evento["type"]
    dados = evento["data"]["object"]

    if tipo == "checkout.session.completed":
        ref_id = dados.get("client_reference_id") or dados.get("metadata", {}).get("usuario_id")
        if ref_id and str(ref_id).isdigit():
            usuario = db.query(Usuario).filter(Usuario.id == int(ref_id)).first()
            if usuario:
                usuario.plano = "pro"
                usuario.status_assinatura = "ativa"
                usuario.gateway_cliente_id = dados.get("customer")
                usuario.gateway_assinatura_id = dados.get("subscription")
                usuario.assinatura_expira_em = None
                db.commit()

    elif tipo in {"customer.subscription.deleted", "invoice.payment_failed"}:
        customer_id = dados.get("customer")
        if customer_id:
            usuario = db.query(Usuario).filter(Usuario.gateway_cliente_id == customer_id).first()
            if usuario:
                usuario.plano = "free"
                usuario.status_assinatura = "cancelada" if tipo == "customer.subscription.deleted" else "atrasada"
                db.commit()

    return {"recebido": True}