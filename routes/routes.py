import os
import tempfile
from datetime import datetime
from math import isfinite

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
from repositories.integracao_usuario_repository import buscar_integracao_principal

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

    dados_validados = validar_dados(dados_ia)

    resultado_mcp = await servico.registrar_transacao(dados_ia)

    if isinstance(resultado_mcp, dict) and resultado_mcp.get("erro"):
        raise HTTPException(status_code=502, detail=resultado_mcp["erro"])

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

    return salvar_financa(db, usuario_id, dados_validados, referencia_externa)

async def registrar_texto_local(
        texto: str, usuario_id: int, db: Session,
):
    dados_ia = extrair_colunas(texto, [])
    dados_validados = validar_dados(dados_ia)

    return salvar_financa(db, usuario_id, dados_validados)


async def registrar_conforme_integracao(texto, usuario_id, db):
    provedor = buscar_integracao_principal(usuario_id)

    if provedor == "local":
        return await registrar_texto_local(texto, usuario_id, db)
    elif provedor == "minhas_economias":
        return await registrar_texto_financeiro(texto, usuario_id, db)

    raise HTTPException(status_code=409, detail="Deve ser informado o banco de armazenamento dos dados")


def validar_dados(dados):
    if not isinstance(dados, dict):
            raise HTTPException(status_code=502, detail="Resposta inváida da extração")

    if dados.get("tipo") != "GASTO":
        raise HTTPException(status_code=422, detail="MVP aceita somente gastos")

    try:
        valor = float(dados["valor"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Valor inválido") from None

    if not isfinite(valor) or valor <= 0:
        raise HTTPException(status_code=422, detail="Valor deve ser positivo e finito")

    data_ia = dados.get('data')

    try:
        data_obj = datetime.strptime(data_ia, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Data inválida") from None

    return {
    "valor": valor,
    "categoria": dados.get("categoria") or "Outros",
    "descricao": dados.get("descricao") or "Sem descrição",
    "tipo": "GASTO",
    "data": data_obj}
    

def salvar_financa(db: Session, usuario_id: int, dados: dict, referencia_externa: str | None = None) -> model.Financa: 
    usuario = (db.query(model.Usuario).filter(model.Usuario.id == usuario_id, model.Usuario.ativo.is_(True)).with_for_update().first())

    if not usuario:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    
    novo_item = model.Financa(
        usuario_id=usuario_id,
        valor = dados['valor'],
        categoria = dados['categoria'],
        descricao = dados['descricao'],
        tipo = dados['tipo'],
        data = dados["data"],
        numero_usuario = usuario.proximo_numero_transacao,
        referencia_externa=referencia_externa)

    usuario.proximo_numero_transacao += 1

    usuario.saldo -= dados["valor"]

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

        return await registrar_conforme_integracao(texto, usuario_id, db)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@router.post('/financas', response_model=ResponseFinanca)
async def adicionar_dados(request: RequestFinanca, db: Session = Depends(get_db)):
    usuario_id = buscar_usuario_id_por_identidade(request.provedor, request.identificador_externo)

    if not usuario_id:
        raise HTTPException(status_code=403, detail='identidade não autorizada')
    return await registrar_conforme_integracao(request.texto, usuario_id, db)

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

    if transacao.referencia_externa:
        servico = await obter_finance_service(usuario_id)
        if isinstance(servico, dict) and servico.get("erro"):
            raise HTTPException(status_code=503, detail=servico.get("erro"))
    
        resultado_exclusao = await servico.excluir_transacao(transacao.referencia_externa)
    
        if(
            isinstance(resultado_exclusao, dict) and resultado_exclusao.get("erro")
        ):
            raise HTTPException(status_code=502, detail=resultado_exclusao.get("erro"))

    usuario = (db.query(model.Usuario).filter(model.Usuario.id == usuario_id, model.Usuario.ativo.is_(True)).with_for_update().first())

    if not usuario:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    
    if transacao.tipo == "GASTO":
        usuario.saldo += transacao.valor
    elif transacao.tipo == "GANHO":
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

    if transacao.tipo != "GASTO":
        raise HTTPException(
            status_code=422,
            detail="Edição de ganhos ainda indisponível",
        )

    texto = transacao_nova.texto

    dados_ia = extrair_colunas(texto)

    dados_validados = validar_dados(dados_ia)

    if transacao.referencia_externa:
        servico = await obter_finance_service(usuario_id)

        if isinstance(servico, dict) and servico.get('erro'):
            raise HTTPException(status_code=503, detail=servico.get('erro'))

        resultado_edicao = await servico.editar_transacao(transacao.referencia_externa, dados_ia)

        if(isinstance(resultado_edicao, dict) and resultado_edicao.get('erro')):
            raise HTTPException(status_code=502, detail=resultado_edicao.get('erro'))

    usuario = (db.query(model.Usuario).filter(model.Usuario.id == usuario_id, model.Usuario.ativo.is_(True)).with_for_update().first())

    if not usuario:
        raise HTTPException(status_code=404, detail='Usuário não encontrado')

    usuario.saldo += transacao.valor

    transacao.valor = dados_validados["valor"]
    transacao.categoria = dados_validados["categoria"]
    transacao.descricao = dados_validados["descricao"]

    usuario.saldo -= transacao.valor

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