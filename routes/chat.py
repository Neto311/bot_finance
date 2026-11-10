import os
import tempfile
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from dependencies.autenticacao_servico import validar_servico
from dependencies.identidade import obter_usuario_id_atual
from models.chat import MensagemChat
from schemas.chat import (
    RequestMensagemTexto,
    ResponseEnvioChat,
    ResponseHistoricoChat,
)
from services.chat_service import processar_mensagem_usuario
from services.groq_client import extrair_audio

chat_router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(validar_servico)],
)

@chat_router.get("/mensagens", response_model=ResponseHistoricoChat)
def listar_mensagens(
    cursor: int | None = Query(default=None),
    limite: int = Query(default=30, ge=1, le=100),
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db),
):
    consulta = db.query(MensagemChat).filter(MensagemChat.usuario_id == usuario_id)
    if cursor is not None:
        consulta = consulta.filter(MensagemChat.id < cursor)
    registros = consulta.order_by(MensagemChat.id.desc()).limit(limite + 1).all()
    tem_mais = len(registros) > limite
    mensagens_pagina = registros[:limite]
    mensagens_pagina.reverse()
    proximo_cursor = mensagens_pagina[0].id if (tem_mais and mensagens_pagina) else None
    return {
        "mensagens": mensagens_pagina,
        "tem_mais": tem_mais,
        "proximo_cursor": proximo_cursor,
    }

@chat_router.post("/texto", response_model=ResponseEnvioChat)
async def enviar_texto(
    dados: RequestMensagemTexto,
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db),
):
    msg_usuario, msg_assistente = await processar_mensagem_usuario(
        texto=dados.texto,
        usuario_id=usuario_id,
        db=db,
    )
    return {
        "mensagem_usuario": msg_usuario,
        "mensagem_assistente": msg_assistente,
    }
@chat_router.post("/audio", response_model=ResponseEnvioChat)
async def enviar_audio(
    file: UploadFile = File(...),
    duracao_segundos: int | None = Form(default=None),
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db),
):
    extensao = os.path.splitext(file.filename or "")[1] or ".m4a"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=extensao, delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await file.read())
        texto_transcrito = (extrair_audio(temp_path) or "").strip()
        if not texto_transcrito:
            raise HTTPException(status_code=422, detail="Não foi possível transcrever o áudio")
        msg_usuario, msg_assistente = await processar_mensagem_usuario(
            texto=texto_transcrito,
            usuario_id=usuario_id,
            db=db,
            tipo_entrada="audio",
            dados_extras_usuario={"duracao_segundos": duracao_segundos},
        )
        return {
            "mensagem_usuario": msg_usuario,
            "mensagem_assistente": msg_assistente,
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)