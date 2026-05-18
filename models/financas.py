from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
from datetime import datetime


class Financa(Base):
    __tablename__ = "financas"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    categoria = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    data = Column(DateTime, default=datetime.now)

    