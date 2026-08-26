from pydantic import BaseModel
from datetime import datetime


class RequestFinanca(BaseModel):
    texto: str
    provedor: str
    identificador_externo: str

class ResponseFinanca(BaseModel):
    id: int
    valor: float
    categoria: str
    descricao: str
    tipo: str
    data: datetime

class Usuario(BaseModel):
    saldo: float

class RequestAtualizarFinanca(BaseModel):
    texto: str