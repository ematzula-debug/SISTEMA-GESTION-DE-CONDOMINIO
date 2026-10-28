import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/condominio"
)

# Acepta la dirección tal como la entrega Supabase o Render (postgresql://...)
for prefijo in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(prefijo):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(prefijo):]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
