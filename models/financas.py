from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from database import Base
from datetime import datetime


class Financa(Base):
    __tablename__ = "financas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    valor = Column(Float, nullable=False)
    categoria = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    data = Column(DateTime, default=datetime.now)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    saldo = Column(Float, default=0.0)

class IdentidadeExterna(Base):
    __tablename__ = 'identidades_externas'

    __table_args__ = (UniqueConstraint(
        'provedor','identificador_externo',
        name = 'uq_identidade_provedor_identificador'
    ),)

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    provedor = Column(String, nullable=False)
    identificador_externo = Column(String, nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)

