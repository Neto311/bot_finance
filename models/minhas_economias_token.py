from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database import Base
from datetime import datetime

class MinhasEconomiasToken(Base):
    __tablename__ = 'minhas_economias_token'

    id = Column(Integer, primary_key=True, nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_type = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)