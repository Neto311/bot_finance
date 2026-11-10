from datetime import datetime 
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class RequestMensagemTexto(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)

class ResponseMensagemChat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remetente: str
    tipo: str
    conteudo: str
    dados_extras: dict[str, Any] | None=None
    criado_em: datetime

class ResponseEnvioChat(BaseModel):
    mensagem_usuario: ResponseMensagemChat
    mensagem_assistente: ResponseMensagemChat

class ResponseHistoricoChat(BaseModel):
    mensagens: list[ResponseMensagemChat]
    tem_mais: bool
    proximo_cursor: int | None=None

