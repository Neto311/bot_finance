from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from database import Base
from datetime import datetime


class Financa(Base):
    __tablename__ = "financas"

    __table_args__ = (UniqueConstraint("usuario_id", "numero_usuario", name="uq_financa_usuario_numero"),)

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, index=True)
    valor = Column(Float, nullable=False)
    categoria = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    data = Column(DateTime, default=datetime.now)
    referencia_externa = Column(String, nullable=True, index=True)
    numero_usuario = Column(Integer, nullable=False)
    origem = Column(String, nullable=True)
    grupo_parcelamento_id = Column(String(36), nullable=True, index=True)
    parcela_atual = Column(Integer, nullable=True)
    parcela_total = Column(Integer, nullable=True)
    recorrencia_id = Column(Integer, ForeignKey("recorrencias.id", ondelete="SET NULL"), nullable=True, index=True)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    senha_hash = Column(String, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    saldo = Column(Float, default=0.0)
    proximo_numero_transacao = Column(Integer, nullable=False, default=1)
    codigo_recuperacao = Column(String(6), nullable=True)
    codigo_recuperacao_expira_em = Column(DateTime, nullable=True)
    plano = Column(String(20), nullable=False, default="free", server_default="free")
    status_assinatura = Column(String(30), nullable=False, default="inativa", server_default="inativa")
    assinatura_expira_em = Column(DateTime, nullable=True)
    gateway_cliente_id = Column(String(120), nullable=True)
    gateway_assinatura_id = Column(String(120), nullable=True)

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


class Recorrencia(Base):
    __tablename__ = "recorrencias"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    valor = Column(Float, nullable=False)
    categoria = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    tipo = Column(String, nullable=False, default="GASTO")
    dia_vencimento = Column(Integer, nullable=False)
    ativa = Column(Boolean, nullable=False, default=True)
    ultima_competencia  = Column(String(7), nullable=True)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)