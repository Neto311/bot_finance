import os
import tempfile
from datetime import datetime

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    UploadFile,
)
from sqlalchemy import extract
from sqlalchemy.orm import Session

from database import get_db
from dependencies.autenticacao_servico import validar_servico
from dependencies.identidade import obter_usuario_id_atual
from models import financas as model
from repositories.identidade_externa_repository import buscar_usuario_id_por_identidade
from schemas.financas import (
    RequestAtualizarFinanca,
    RequestFinanca,
    ResponseFinanca,
    Usuario,
)
from services.finance_service_factory import obter_finance_service
from services.groq_client import extrair_audio, extrair_colunas

router = APIRouter(dependencies=[Depends(validar_servico)])

async def registrar_texto_financeiro(
    texto: str,
    usuario_id: int,
    db: Session):

    servico= await obter_finance_service(usuario_id)

    if isinstance(servico, dict) and servico.get('erro'):
        raise HTTPException(status_code=503, detail=servico.get('erro'))

    catalogo = await servico.montar_catalogo_categorias('GASTO')

    if isinstance(catalogo, dict) and catalogo.get('erro'):
        raise HTTPException(status_code=502, detail = catalogo.get('erro'))

    dados_ia = extrair_colunas(texto, catalogo)

    if not isinstance(dados_ia, dict):
        raise HTTPException(status_code=502)

    if dados_ia.get('tipo') != 'GASTO':
        raise HTTPException(status_code=422, detail='MVP aceita somente gastos')

    resultado_mcp = await servico.registrar_transacao(dados_ia)

    if not isinstance(resultado_mcp, list) or not resultado_mcp:
        raise HTTPException(
            status_code=502,
            detail="Resposta inesperada do Minhas Economias"
        )

    transacao_mcp = resultado_mcp[0]

    if not isinstance(transacao_mcp, dict):
        raise HTTPException(
            status_code=502,
            detail="Transação externa em formato inesperado"
        )

    referencia_externa = transacao_mcp.get("transactionRef")

    if not referencia_externa:
        raise HTTPException(
            status_code=502,
            detail="Minhas Economias não retornou a referência da transação"
        )


    if isinstance(resultado_mcp, dict) and resultado_mcp.get('erro'):
        raise HTTPException(status_code=502, detail=resultado_mcp.get('erro'))

    if not resultado_mcp:
        raise HTTPException(status_code=502, detail='Minhas economias não confirmou a criação')

    usuario = (db.query(model.Usuario).filter(model.Usuario.id == usuario_id, model.Usuario.ativo.is_(True)).with_for_update().first())

    if not usuario:
        raise HTTPException(status_code=403)

    data_ia = dados_ia.get('data')

    if isinstance(data_ia, str):
        data_obj = datetime.strptime(data_ia, '%Y-%m-%d')
    else:
        data_obj = datetime.now()

    novo_item = model.Financa(
        usuario_id=usuario_id,
        valor = dados_ia.get('valor') or 0.0,
        categoria = dados_ia.get('categoria') or "Outros",
        descricao = dados_ia.get('descricao') or "Sem descrição",
        tipo = dados_ia.get('tipo') or "GASTO",
        data = data_obj,
        numero_usuario = usuario.proximo_numero_transacao,
        referencia_externa=referencia_externa
    )

    usuario.proximo_numero_transacao += 1

    if novo_item.tipo == "GASTO":
        usuario.saldo -= novo_item.valor
    elif novo_item.tipo == "GANHO":
        usuario.saldo += novo_item.valor


    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)

    return novo_item

@router.post('/financas/audio', response_model=ResponseFinanca)
async def processar_audio(file: UploadFile = File(...), provedor: str = Form(...), identificador_externo: str =Form(...), db: Session = Depends(get_db)):
    usuario_id = buscar_usuario_id_por_identidade(provedor, identificador_externo)

    if not usuario_id:
        raise HTTPException(status_code=403, detail='identidade não autorizada')

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as arquivo_temporario:
            temp_path = arquivo_temporario.name
            arquivo_temporario.write(await file.read())

        texto = extrair_audio(temp_path)

        return await registrar_texto_financeiro(texto, usuario_id, db)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@router.post('/financas', response_model=ResponseFinanca)
async def adicionar_dados(request: RequestFinanca, db: Session = Depends(get_db)):
    usuario_id = buscar_usuario_id_por_identidade(request.provedor, request.identificador_externo)

    if not usuario_id:
        raise HTTPException(status_code=403, detail='identidade não autorizada')
    return await registrar_texto_financeiro(request.texto, usuario_id, db)

@router.get ('/financas', response_model = list[ResponseFinanca])
def ver_itens(
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db)
):

    dados = (db.query(model.Financa).filter(model.Financa.usuario_id == usuario_id).all())

    return dados


@router.put('/saldo', response_model=Usuario)
def atualizar_saldo(
    novo_saldo: Usuario,
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db)
):
    usuario = db.query(model.Usuario).filter(model.Usuario.id == usuario_id ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail='Usuário não encontrado')

    usuario.saldo = novo_saldo.saldo
    db.commit()
    db.refresh(usuario)

    return usuario

@router.get('/saldo', response_model=list[Usuario])
def ver_saldo(
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db)
):
    usuario = db.query(model.Usuario).filter(model.Usuario.id == usuario_id ).all()

    return usuario


@router.delete('/financas/{numero_usuario}')
async def deletar_transacao(
    numero_usuario: int,
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db)
):

    transacao = db.query(model.Financa).filter(model.Financa.numero_usuario == numero_usuario, model.Financa.usuario_id == usuario_id).first()

    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    usuario = (db.query(model.Usuario).filter(model.Usuario.id == usuario_id, model.Usuario.ativo.is_(True)).first())

    if not transacao.referencia_externa:
        raise HTTPException(status_code=409, detail=("Transação local sem referência externa; " "exclusão automática indisponível"))

    servico = await obter_finance_service(usuario_id)

    if isinstance(servico, dict) and servico.get("erro"):
        raise HTTPException(status_code=503, detail=servico.get("erro"))

    resultado_exclusao = await servico.excluir_transacao(transacao.referencia_externa)

    if(
        isinstance(resultado_exclusao, dict) and resultado_exclusao.get("erro")
    ):
        raise HTTPException(status_code=502, detail=resultado_exclusao.get("erro"))

    if usuario and transacao.tipo == "GASTO":
        usuario.saldo += transacao.valor
    elif usuario and transacao.tipo == "GANHO":
        usuario.saldo -= transacao.valor

    db.delete(transacao)
    db.commit()

    return {'mensagem': 'transacao deletada com sucesso'}


@router.put('/financas/{numero_usuario}', response_model=ResponseFinanca)
async def atualizar_transacao(
    numero_usuario: int = Path(...),
    usuario_id: int = Depends(obter_usuario_id_atual),
    transacao_nova: RequestAtualizarFinanca = Body(...),
    db: Session = Depends(get_db)):

    transacao = db.query(model.Financa).filter(model.Financa.numero_usuario == numero_usuario, model.Financa.usuario_id == usuario_id).first()

    if not transacao:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    texto = transacao_nova.texto

    dados_ia = extrair_colunas(texto)

    servico = await obter_finance_service(usuario_id)

    if isinstance(servico, dict) and servico.get('erro'):
        raise HTTPException(status_code=503, detail=servico.get('erro'))

    if not transacao.referencia_externa:
        raise HTTPException(status_code=409, detail='Transacao local sem referencia externa')

    resultado_edicao = await servico.editar_transacao(transacao.referencia_externa, dados_ia)

    if(isinstance(resultado_edicao, dict) and resultado_edicao.get('erro')):
        raise HTTPException(status_code=502, detail=resultado_edicao.get('erro'))

    usuario = (db.query(model.Usuario).filter(model.Usuario.id == usuario_id).with_for_update().first())

    if not usuario:
        raise HTTPException(status_code=404, detail='Usuário não encontrado')

    if usuario and transacao.tipo == "GASTO":
        usuario.saldo += transacao.valor
    elif usuario and transacao.tipo == "GANHO":
        usuario.saldo -= transacao.valor

    transacao.valor = float(dados_ia.get('valor'))
    transacao.categoria = dados_ia.get('categoria')
    transacao.descricao = dados_ia.get('descricao')

    if usuario and transacao.tipo == "GASTO":
        usuario.saldo -= transacao.valor
    elif usuario and transacao.tipo == "GANHO":
        usuario.saldo += transacao.valor

    db.commit()
    db.refresh(transacao)

    return transacao



@router.get('/financas/data')
def ver_transacao_data(
    mes: int,
    ano: int,
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db)
):
    dados = db.query(model.Financa).filter(
        extract('month', model.Financa.data) == mes,
        extract('year', model.Financa.data) == ano,
        model.Financa.usuario_id == usuario_id
    ).all()

    return dados


@router.get('/resumo')
def resumo(
    mes: int,
    ano: int,
    usuario_id: int = Depends(obter_usuario_id_atual),
    db: Session = Depends(get_db)):

    dados = db.query(model.Financa).filter(
        extract('month', model.Financa.data) == mes,
        extract('year', model.Financa.data) == ano,
        model.Financa.usuario_id == usuario_id
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


