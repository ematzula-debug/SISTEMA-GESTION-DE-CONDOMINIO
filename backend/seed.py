"""Crea las tablas, un usuario administrador y viviendas de ejemplo.

Uso:  python seed.py
"""
import os
from getpass import getpass

from sqlalchemy import select

from app import models as m
from app.database import Base, SessionLocal, engine
from app.security import hash_password

CORREO_ADMIN = "admin@condominio.com"
VIVIENDAS = [
    ("A-101", "Torre A", "Apartamento", 78, "Ocupada"),
    ("A-102", "Torre A", "Apartamento", 78, "Ocupada"),
    ("B-201", "Torre B", "Apartamento", 92, "Disponible"),
    ("C-07", "Casas", "Casa", 140, "Ocupada"),
]

Base.metadata.create_all(engine)

with SessionLocal() as db:
    if not db.scalar(select(m.Usuario).where(m.Usuario.correo == CORREO_ADMIN)):
        password = os.getenv("ADMIN_PASSWORD") or getpass(
            f"Contraseña para {CORREO_ADMIN} (mínimo 8 caracteres): "
        )
        if len(password) < 8:
            raise SystemExit("La contraseña debe tener al menos 8 caracteres.")
        db.add(
            m.Usuario(
                nombre="Administrador",
                rol="Administrador",
                correo=CORREO_ADMIN,
                password_hash=hash_password(password),
            )
        )
    for codigo, bloque, tipo, area, estado in VIVIENDAS:
        if not db.scalar(select(m.Vivienda).where(m.Vivienda.codigo == codigo)):
            db.add(m.Vivienda(codigo=codigo, bloque=bloque, tipo=tipo, area=area, estado=estado))
    db.commit()

print("Listo: tablas creadas y datos iniciales cargados.")
