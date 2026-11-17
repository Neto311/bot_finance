from datetime import datetime, date
from fastapi import HTTPException
from sqlalchemy import extract
from sqlalchemy.orm import Session

from models.chat import MensagemChat
from models.financas import Usuario

LIMITE_MENSAGENS_FREE = 30


def usuario_eh_pro(usuario: Usuario | None) -> bool:
    if not usuario or usuario.plano != "pro":
        return False
    if usuario.status_assinatura not in {"ativa", "trial"}:
        return False
    if usuario.assinatura_expira_em and usuario.assinatura_expira_em < datetime.now():
        return False
    return True


def contar_mensagens_mes(db: Session, usuario_id: int) -> int:
    hoje = date.today()
    return (
        db.query(MensagemChat)
        .filter(
            MensagemChat.usuario_id == usuario_id,
            MensagemChat.remetente == "usuario",
            extract("month", MensagemChat.criado_em) == hoje.month,
            extract("year", MensagemChat.criado_em) == hoje.year,
        )
        .count()
    )


def exigir_plano_pro(db: Session, usuario_id: int, recurso: str = "Este recurso") -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not usuario_eh_pro(usuario):
        raise HTTPException(
            status_code=402,
            detail=f"{recurso} é exclusivo do plano FinaceAi Pro.",
        )
    return usuario


def verificar_limite_chat_texto(db: Session, usuario_id: int) -> None:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if usuario_eh_pro(usuario):
        return
    usadas = contar_mensagens_mes(db, usuario_id)
    if usadas >= LIMITE_MENSAGENS_FREE:
        raise HTTPException(
            status_code=402,
            detail=f"Você atingiu o limite de {LIMITE_MENSAGENS_FREE} mensagens do plano gratuito este mês. Assine o FinaceAi Pro para continuar!",
        )