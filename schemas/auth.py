from pydantic import BaseModel, EmailStr, Field

class RequestRegistro(BaseModel):
    nome: str = Field(min_length=2, max_length=129)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)

class RequestLogin(BaseModel):
    email: EmailStr
    senha: str

class RequestGoogleAuth(BaseModel):
    id_token: str

class RequestRefresh(BaseModel):
    refresh_token: str

class ResponseUsuarioAuth(BaseModel):
    id: int
    nome: str
    email: str
    saldo: float
    provedor_principal: str | None = None

class ResponseTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: ResponseUsuarioAuth

class RequestEsqueciSenha(BaseModel):
    email: EmailStr

class RequestRedefinirSenha(BaseModel):
    email: EmailStr
    codigo: str = Field(min_length=6, max_length=6)
    nova_senha: str = Field(min_length=8, max_length=128) 