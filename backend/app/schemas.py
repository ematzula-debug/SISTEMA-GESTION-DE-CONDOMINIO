from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before")
    @classmethod
    def vacio_a_none(cls, v):
        # El frontend envía "" en los campos opcionales vacíos
        return None if v == "" else v


class Login(BaseModel):
    correo: str
    password: str


# ---- Usuarios ----
class UsuarioBase(Base):
    nombre: str
    rol: Literal["Administrador", "Propietario", "Inquilino", "Guardia"]
    correo: str
    telefono: str | None = None
    vivienda: str | None = None


class UsuarioIn(UsuarioBase):
    password: str | None = Field(default=None, min_length=8)


class UsuarioOut(UsuarioBase):
    id: UUID


# ---- Viviendas ----
class ViviendaIn(Base):
    codigo: str
    bloque: str | None = None
    tipo: Literal["Apartamento", "Casa"]
    area: float | None = None
    estado: Literal["Ocupada", "Disponible"] = "Disponible"


class ViviendaOut(ViviendaIn):
    id: UUID


# ---- Propietarios ----
class PropietarioIn(Base):
    nombre: str
    documento: str | None = None
    telefono: str | None = None
    correo: str | None = None
    vivienda: str | None = None


class PropietarioOut(PropietarioIn):
    id: UUID


# ---- Pagos ----
class PagoIn(Base):
    vivienda: str
    concepto: Literal["Cuota de mantenimiento", "Cuota extraordinaria", "Multa"]
    monto: float = Field(gt=0)
    mes: str = Field(pattern=r"^\d{4}-\d{2}$")
    estado: Literal["Pendiente", "Pagado", "Vencido"] = "Pendiente"


class PagoOut(PagoIn):
    id: UUID


# ---- Visitas ----
class VisitaIn(Base):
    visitante: str
    documento: str | None = None
    vivienda: str
    motivo: str | None = None
    entrada: datetime
    estado: Literal["Dentro", "Salió"] = "Dentro"


class VisitaOut(VisitaIn):
    id: UUID


# ---- Mantenimiento ----
class MantenimientoIn(Base):
    titulo: str
    vivienda: str | None = None
    prioridad: Literal["Baja", "Media", "Alta"] = "Media"
    estado: Literal["Abierta", "En proceso", "Resuelta"] = "Abierta"
    descripcion: str | None = None


class MantenimientoOut(MantenimientoIn):
    id: UUID
