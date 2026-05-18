from pydantic import BaseModel
from datetime import datetime


class RequestFinanca(BaseModel):
    texto: str


class ResponseFinanca(BaseModel):
    id: int
    valor: float
    categoria: str
    descricao: str
    data: datetime