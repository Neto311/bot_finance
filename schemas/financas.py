from datetime import datetime

from pydantic import BaseModel


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
    numero_usuario: int

class Usuario(BaseModel):
    saldo: float

class RequestAtualizarFinanca(BaseModel):
    texto: str