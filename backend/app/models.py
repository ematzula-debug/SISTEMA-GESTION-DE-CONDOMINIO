import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    creado: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


def fk_vivienda(nullable: bool):
    return mapped_column(
        String(20),
        ForeignKey("viviendas.codigo", onupdate="CASCADE"),
        nullable=nullable,
        index=True,
    )


class Vivienda(IdMixin, Base):
    __tablename__ = "viviendas"
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    bloque: Mapped[str | None] = mapped_column(String(60))
    tipo: Mapped[str] = mapped_column(String(20))
    area: Mapped[float | None] = mapped_column(Numeric(8, 2))
    estado: Mapped[str] = mapped_column(String(20), default="Disponible")


class Usuario(IdMixin, Base):
    __tablename__ = "usuarios"
    nombre: Mapped[str] = mapped_column(String(120))
    rol: Mapped[str] = mapped_column(String(20))
    correo: Mapped[str] = mapped_column(String(160), unique=True)
    telefono: Mapped[str | None] = mapped_column(String(30))
    vivienda: Mapped[str | None] = fk_vivienda(True)
    password_hash: Mapped[str | None] = mapped_column(String(100))


class Propietario(IdMixin, Base):
    __tablename__ = "propietarios"
    nombre: Mapped[str] = mapped_column(String(120))
    documento: Mapped[str | None] = mapped_column(String(30), unique=True)
    telefono: Mapped[str | None] = mapped_column(String(30))
    correo: Mapped[str | None] = mapped_column(String(160))
    vivienda: Mapped[str | None] = fk_vivienda(True)


class Pago(IdMixin, Base):
    __tablename__ = "pagos"
    vivienda: Mapped[str] = fk_vivienda(False)
    concepto: Mapped[str] = mapped_column(String(40))
    monto: Mapped[float] = mapped_column(Numeric(10, 2))
    mes: Mapped[str] = mapped_column(String(7))  # AAAA-MM
    estado: Mapped[str] = mapped_column(String(20), default="Pendiente")


class Visita(IdMixin, Base):
    __tablename__ = "visitas"
    visitante: Mapped[str] = mapped_column(String(120))
    documento: Mapped[str | None] = mapped_column(String(30))
    vivienda: Mapped[str] = fk_vivienda(False)
    motivo: Mapped[str | None] = mapped_column(String(160))
    entrada: Mapped[datetime] = mapped_column(DateTime)
    estado: Mapped[str] = mapped_column(String(20), default="Dentro")


class Mantenimiento(IdMixin, Base):
    __tablename__ = "mantenimiento"
    titulo: Mapped[str] = mapped_column(String(160))
    # Ubicación libre: una vivienda o un área común, por eso no es llave foránea
    vivienda: Mapped[str | None] = mapped_column(String(60))
    prioridad: Mapped[str] = mapped_column(String(10), default="Media")
    estado: Mapped[str] = mapped_column(String(20), default="Abierta")
    descripcion: Mapped[str | None] = mapped_column(Text)
