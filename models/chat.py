from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from database import Base
from datetime import datetime

class MensagemChat(Base):
    __tablename__ = "mensagens_chat"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    remetente = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    conteudo = Column(Text, nullable=False)
    dados_extras = Column(JSON, nullable=True)  
    criado_em = Column(DateTime, default=datetime.now, nullable=False, index=True)