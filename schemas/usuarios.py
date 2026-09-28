from pydantic import BaseModel
from typing import Literal


class RequestOnboarding(BaseModel):
    provedor: str
    identificador_externo: str
    nome: str

class RequestSelecionarIntegracao(BaseModel):
    provedor: Literal["local", "minhas_economias"]
