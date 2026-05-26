from fastapi import APIRouter, Depends, UploadFile, File
from services.groq_client import extrair_colunas, extrair_audio
from database import get_db
from models.financas import Financa
from models.financas import Usuario
from sqlalchemy.orm import Session
from schemas.financas import ResponseFinanca, RequestFinanca, Usuario
from models import financas as model
from datetime import datetime 
import os



router = APIRouter()

@router.post('/financas', response_model=ResponseFinanca)
def adicionar_dados(
    request: RequestFinanca,
    db: Session = Depends(get_db)):

    usuario = db.query(model.Usuario).first()

    if not usuario:
        novo_usuario = model.Usuario(saldo = 0.0)
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

    texto = request.texto

    dados_ia = extrair_colunas(texto)

    data_ia = dados_ia.get('data')

    if isinstance(data_ia, str):
        data_obj = datetime.strptime(data_ia, '%Y-%m-%d')
    else:
        data_obj = datetime.now()
    
    novo_item = model.Financa(
        valor = dados_ia.get('valor') or 0.0,
        categoria = dados_ia.get('categoria') or "Outros",
        descricao = dados_ia.get('descricao') or "Sem descrição",
        tipo = dados_ia.get('tipo') or "Crédito",
        data = data_obj,
    )
    
    condicao = "Débito"

    if novo_item.tipo.lower().strip() == condicao.lower().strip():
        usuario = db.query(model.Usuario).first()
        if usuario:
            usuario.saldo -= novo_item.valor
            db.commit()
            db.refresh(usuario)
        elif usuario == None:
            novo_usuario = model.Usuario(saldo = -novo_item.valor)
            db.add(novo_usuario)
            db.commit()
            db.refresh(novo_usuario)
    
        
    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)

    return novo_item

@router.post('/financas/audio')
async def processar_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        temp_path = f'temp_{file.filename}'
        with open(temp_path, 'wb') as f:
            f.write(await file.read())
        
        texto = extrair_audio(temp_path)
        dados_ia = extrair_colunas(texto)

        data_ia = dados_ia.get('data')

        if isinstance(data_ia, str):
            data_obj = datetime.strptime(data_ia, '%Y-%m-%d')
        else:
            data_obj = datetime.now()
        
        novo_item = model.Financa(
            valor = dados_ia.get('valor') or 0.0,
            categoria = dados_ia.get('categoria') or "Outros",
            descricao = dados_ia.get('descricao') or "Sem descrição",
            tipo = dados_ia.get('tipo') or "Crédito",
            data = data_obj,
        )
        
        condicao = "Débito"

        if novo_item.tipo.lower().strip() == condicao.lower().strip():
            usuario = db.query(model.Usuario).first()
            if usuario:
                usuario.saldo -= novo_item.valor
                db.commit()
                db.refresh(usuario)
            elif usuario == None:
                novo_usuario = model.Usuario(saldo = -novo_item.valor)
                db.add(novo_usuario)
                db.commit()
                db.refresh(novo_usuario)
        
            
        db.add(novo_item)
        db.commit()
        db.refresh(novo_item)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return novo_item


@router.get ('/financas', response_model = list[ResponseFinanca])
def ver_itens(
    db: Session = Depends(get_db)
):
    dados = db.query(model.Financa).all()

    return dados


@router.put('/saldo', response_model=Usuario)
def atualizar_saldo(
    novo_saldo: Usuario,
    db: Session = Depends(get_db)
):
    usuario = db.query(model.Usuario).first()
    if usuario:
        usuario.saldo = novo_saldo.saldo
        db.commit()
        db.refresh(usuario)
    
    if not usuario:
        novo_usuario = model.Usuario(saldo = novo_saldo.saldo)
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
    
    return usuario or novo_usuario

@router.get('/saldo', response_model=list[Usuario])
def ver_saldo(
    db: Session = Depends(get_db)
):
    usuario = db.query(model.Usuario).all()

    return usuario
