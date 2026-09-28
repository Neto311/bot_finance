from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)

from database import Base


class IntegracaoUsuario(Base):
    __tablename__ = "integracoes_usuario"

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "provedor",
            name="uq_integracao_usuario_provedor"
        ),
        Index(
            "uq_integracao_principal_por_usuario",
            "usuario_id",
            unique=True,
            postgresql_where=text("principal = true"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    provedor = Column(String, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    principal = Column(Boolean, nullable=False, default=False)
    criado_em = Column(DateTime, nullable=False, default=datetime.now)