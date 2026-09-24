from pydantic import BaseModel


class RequestOnboarding(BaseModel):
    provedor: str
    identificador_externo: str
    nome: str
