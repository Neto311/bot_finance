import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Tenta pegar DATABASE_URL (padrão do Render/Neon) ou DATA_BASE (seu padrão antigo)
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATA_BASE")

# Correção para o SQLAlchemy: Postgres precisa começar com 'postgresql://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Se não houver nada, usa SQLite local
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./financas.db"

engine = create_engine(DATABASE_URL)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()