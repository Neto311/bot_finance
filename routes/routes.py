from fastapi import APIRouter, Depends
from services.groq_client import extrair_colunas
from database import get_db
from models.financas import Financa
from sqlalchemy.orm import Session
from schemas.financas import ResponseFinanca, RequestFinanca
from models import financas as model
from datetime import datetime 



router = APIRouter()

@router.post('/financas', response_model=ResponseFinanca)
def adicionar_dados(
    request: RequestFinanca,
    db: Session = Depends(get_db)):

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
        data = data_obj
    )

    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)

    return novo_item

@router.get ('/financas', response_model = list[ResponseFinanca])
def ver_itens(
    db: Session = Depends(get_db)
):
    dados = db.query(model.Financa).all()
    return dados





