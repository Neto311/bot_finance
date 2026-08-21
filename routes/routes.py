from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Path, Body
from services.groq_client import extrair_colunas, extrair_audio
from database import get_db
from models.financas import Financa
from models.financas import Usuario
from sqlalchemy.orm import Session
from schemas.financas import ResponseFinanca, RequestFinanca, Usuario
from models import financas as model
from datetime import datetime 
import os
from sqlalchemy import select, extract
from services.finance_service_factory import obter_finance_service
import tempfile



router = APIRouter()

@router.post('/financas', response_model=ResponseFinanca)
async def adicionar_dados(
    request: RequestFinanca,
    db: Session = Depends(get_db)):

    servico= await obter_finance_service('usuario_local')

    if isinstance(servico, dict) and servico.get('erro'):
        raise HTTPException(status_code=503, detail=servico.get('erro'))

    catalogo = await servico.montar_catalogo_categorias('GASTO')

    if isinstance(catalogo, dict) and catalogo.get('erro'):
        raise HTTPException(status_code=502, detail = catalogo.get('erro'))

    texto = request.texto

    dados_ia = extrair_colunas(texto, catalogo)

    if not isinstance(dados_ia, dict):
        raise HTTPException(status_code=502)

    if dados_ia.get('tipo') != 'GASTO':
        raise HTTPException(status_code=422, detail='MVP aceita somente gastos')

    resultado_mcp = await servico.registrar_transacao(dados_ia)

    if isinstance(resultado_mcp, dict) and resultado_mcp.get('erro'):
        raise HTTPException(status_code=502, detail=resultado_mcp.get('erro'))

    if not resultado_mcp:
        raise HTTPException(status_code=502, detail='Minhas economias não confirmou a criação')

    usuario = db.query(model.Usuario).first()

    if not usuario:
        novo_usuario = model.Usuario(saldo = 0.0)
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

    

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
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as arquivo_temporario:
            temp_path = arquivo_temporario.name
            arquivo_temporario.write(await file.read())
        
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
        if temp_path and os.path.exists(temp_path):
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


@router.delete('/financas/{id}')
def deletar_transacao(
    id: int,
    db: Session = Depends(get_db)
):
    transacao = db.query(model.Financa).filter(model.Financa.id == id).first()

    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    usuario = db.query(model.Usuario).first()

    if usuario and transacao.tipo.lower() == "débito":
        usuario.saldo += transacao.valor
    elif usuario and transacao.tipo.lower() == "crédito":
        usuario.saldo -= transacao.valor

    db.delete(transacao)
    db.commit()

    return {'mensagem': 'transacao deletada com sucesso'}


@router.put('/financas/{id}', response_model=ResponseFinanca)
def atualizar_transacao(
    id: int = Path(...),
    transacao_nova: RequestFinanca = Body(...),
    db: Session = Depends(get_db)):

    transacao = db.query(model.Financa).filter(model.Financa.id == id).first()

    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    usuario = db.query(model.Usuario).first()

    if usuario:
        if transacao.tipo.lower() == "débito":
            usuario.saldo += transacao.valor
        else:
            usuario.saldo -= transacao.valor


    texto = transacao_nova.texto

    dados_ia = extrair_colunas(texto)

    data_ia = dados_ia.get('data')

    if isinstance(data_ia, str):
        data_obj = datetime.strptime(data_ia, '%Y-%m-%d')
    else:
        data_obj = datetime.now()
    
    transacao.valor = float(dados_ia.get('valor'))
    transacao.categoria = dados_ia.get('categoria')
    transacao.descricao = dados_ia.get('descricao')
    transacao.tipo = dados_ia.get('tipo') or 'Crédito'
    transacao.data = data_obj

    if usuario:
        if transacao.tipo.lower() == "débito":
            usuario.saldo -= transacao.valor
        else:
            usuario.saldo += transacao.valor

    db.commit()
    db.refresh(transacao)

    return transacao



@router.get('/financas/data')
def ver_transacao_data(
    mes: int,
    ano: int,
    db: Session = Depends(get_db)
):
    dados = db.query(model.Financa).filter(
        extract('month', model.Financa.data) == mes,
        extract('year', model.Financa.data) == ano
    ).all()

    return dados


@router.get('/resumo')
def resumo(
    mes: int,
    ano: int,
    db: Session = Depends(get_db)):

    dados = db.query(model.Financa).filter(
        extract('month', model.Financa.data) == mes,
        extract('year', model.Financa.data) == ano
    ).all()

    gasto_total = 0

    categorias = {}

    for i in dados:
        gasto_total += i.valor

        if i.categoria not in categorias:
            categorias[i.categoria] = i.valor
        else:
            categorias[i.categoria] += i.valor

    
    return {
        "mes": mes,
        "ano": ano,
        "gasto_total": gasto_total,
        "categorias": categorias
    }

    
