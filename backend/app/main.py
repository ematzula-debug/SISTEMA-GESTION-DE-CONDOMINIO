import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models as m
from . import schemas as s
from .database import Base, SessionLocal, engine, get_db
from .security import current_user, hash_password, make_token, require, verify_password


def admin_inicial():
    """Si defines ADMIN_PASSWORD y aún no hay administrador, lo crea al arrancar.
    Sirve para Render (plan gratis), donde no hay terminal para correr seed.py."""
    clave = os.getenv("ADMIN_PASSWORD")
    if not clave or len(clave) < 8:
        return
    with SessionLocal() as db:
        if db.scalar(select(m.Usuario).where(m.Usuario.rol == "Administrador")):
            return
        db.add(
            m.Usuario(
                nombre="Administrador",
                rol="Administrador",
                correo=os.getenv("ADMIN_EMAIL", "admin@condominio.com"),
                password_hash=hash_password(clave),
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)  # más adelante: migraciones con Alembic
    admin_inicial()
    yield


app = FastAPI(title="API Gestión de Condominio", lifespan=lifespan)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"]
)


RESIDENTES = ("Propietario", "Inquilino")


def crud(nombre, Model, SIn, SOut, write=None, read_all=None, scope=None,
         prepare=None, residente_crea=False):
    """Genera listar, crear, actualizar y borrar para un módulo.

    write:   roles que pueden crear, editar y borrar (None = cualquier usuario).
    read_all: roles que ven todos los registros (None = cualquier usuario).
    scope:   columna con el código de vivienda. Los residentes (propietario o
             inquilino) solo ven las filas de su vivienda; sin scope no ven el módulo.
    residente_crea: permite a un residente crear registros solo para su vivienda.
    """
    prepare = prepare or (lambda datos: datos.model_dump())
    guard = [Depends(require(*write))] if write else []
    r = APIRouter(
        prefix=f"/api/{nombre}", tags=[nombre], dependencies=[Depends(current_user)]
    )

    def guardar(db: Session):
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                409, "Dato duplicado, vivienda inexistente o registro en uso"
            )

    def buscar(db: Session, id: UUID):
        obj = db.get(Model, id)
        if not obj:
            raise HTTPException(404, "Registro no encontrado")
        return obj

    @r.get("", response_model=list[SOut])
    def listar(user: m.Usuario = Depends(current_user), db: Session = Depends(get_db)):
        consulta = select(Model).order_by(Model.creado)
        if read_all and user.rol not in read_all:
            if not scope:
                raise HTTPException(403, "No tienes permiso para ver este módulo")
            if not user.vivienda:
                return []
            consulta = consulta.where(getattr(Model, scope) == user.vivienda)
        return db.scalars(consulta).all()

    @r.post("", response_model=SOut, status_code=201)
    def crear(
        datos: SIn,
        user: m.Usuario = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        valores = prepare(datos)
        if write and user.rol not in write:
            if not (residente_crea and user.rol in RESIDENTES and user.vivienda):
                raise HTTPException(403, "No tienes permiso para esta acción")
            valores[scope] = user.vivienda  # solo para su propia vivienda
            valores["estado"] = "Abierta"
        obj = Model(**valores)
        db.add(obj)
        guardar(db)
        db.refresh(obj)
        return obj

    @r.put("/{id}", response_model=SOut, dependencies=guard)
    def actualizar(id: UUID, datos: SIn, db: Session = Depends(get_db)):
        obj = buscar(db, id)
        for campo, valor in prepare(datos).items():
            setattr(obj, campo, valor)
        guardar(db)
        db.refresh(obj)
        return obj

    @r.delete("/{id}", status_code=204, dependencies=guard)
    def borrar(id: UUID, db: Session = Depends(get_db)):
        db.delete(buscar(db, id))
        guardar(db)

    app.include_router(r)


def preparar_usuario(datos: s.UsuarioIn) -> dict:
    x = datos.model_dump()
    password = x.pop("password")
    if password:  # si no viene, se conserva la contraseña actual
        x["password_hash"] = hash_password(password)
    return x


ADMIN = ("Administrador",)
STAFF = ("Administrador", "Guardia")
crud("usuarios", m.Usuario, s.UsuarioIn, s.UsuarioOut,
     write=ADMIN, read_all=ADMIN, prepare=preparar_usuario)
crud("propietarios", m.Propietario, s.PropietarioIn, s.PropietarioOut,
     write=ADMIN, read_all=ADMIN)
crud("viviendas", m.Vivienda, s.ViviendaIn, s.ViviendaOut,
     write=ADMIN, read_all=STAFF, scope="codigo")
crud("pagos", m.Pago, s.PagoIn, s.PagoOut,
     write=ADMIN, read_all=ADMIN, scope="vivienda")
crud("visitas", m.Visita, s.VisitaIn, s.VisitaOut,
     write=STAFF, read_all=STAFF, scope="vivienda")
crud("mantenimiento", m.Mantenimiento, s.MantenimientoIn, s.MantenimientoOut,
     write=STAFF, read_all=STAFF, scope="vivienda", residente_crea=True)


@app.get("/api/salud")
def salud():
    return {"estado": "ok"}


@app.post("/api/auth/login")
def login(datos: s.Login, db: Session = Depends(get_db)):
    user = db.scalar(
        select(m.Usuario).where(func.lower(m.Usuario.correo) == datos.correo.lower())
    )
    if not user or not verify_password(datos.password, user.password_hash):
        raise HTTPException(401, "Correo o contraseña incorrectos")
    return {"token": make_token(user.id), "usuario": s.UsuarioOut.model_validate(user)}


@app.get("/api/auth/me", response_model=s.UsuarioOut)
def me(user: m.Usuario = Depends(current_user)):
    return user


@app.get("/api/reportes")
def reportes(user: m.Usuario = Depends(current_user), db: Session = Depends(get_db)):
    if user.rol == "Guardia":
        raise HTTPException(403, "No tienes permiso para ver reportes")
    propio = user.rol in RESIDENTES  # un residente solo ve su vivienda

    def solo_mia(columna):
        return [columna == (user.vivienda or "")] if propio else []

    total = func.coalesce(func.sum(m.Pago.monto), 0)
    por_estado = db.execute(
        select(m.Pago.estado, func.count(), total)
        .where(*solo_mia(m.Pago.vivienda))
        .group_by(m.Pago.estado)
    ).all()
    saldo = db.execute(
        select(m.Pago.vivienda, func.count(), total)
        .where(m.Pago.estado != "Pagado", *solo_mia(m.Pago.vivienda))
        .group_by(m.Pago.vivienda)
    ).all()
    visitas = db.execute(
        select(m.Visita.vivienda, func.count())
        .where(*solo_mia(m.Visita.vivienda))
        .group_by(m.Visita.vivienda)
    ).all()
    mantenimiento = db.execute(
        select(m.Mantenimiento.estado, func.count())
        .where(*solo_mia(m.Mantenimiento.vivienda))
        .group_by(m.Mantenimiento.estado)
    ).all()
    return {
        "pagos_por_estado": [
            {"estado": e, "cantidad": n, "total": float(t)} for e, n, t in por_estado
        ],
        "saldo_por_vivienda": [
            {"vivienda": v, "pagos": n, "saldo": float(t)} for v, n, t in saldo
        ],
        "visitas_por_vivienda": [{"vivienda": v, "visitas": n} for v, n in visitas],
        "mantenimiento_por_estado": [{"estado": e, "cantidad": n} for e, n in mantenimiento],
    }


@app.get("/api/contacto")
def contacto(db: Session = Depends(get_db), _: m.Usuario = Depends(current_user)):
    """Número de WhatsApp de la administración, al que escriben residentes y guardias."""
    numero, nombre = os.getenv("WHATSAPP_NUMERO"), "Administración"
    if not numero:
        admin = db.scalar(
            select(m.Usuario)
            .where(m.Usuario.rol == "Administrador", m.Usuario.telefono.is_not(None))
            .order_by(m.Usuario.creado)
        )
        if admin:
            numero, nombre = admin.telefono, admin.nombre
    digitos = "".join(c for c in (numero or "") if c.isdigit())
    if digitos and len(digitos) <= 8:  # número local: agrega el código de país
        digitos = os.getenv("CODIGO_PAIS", "502") + digitos
    return {"nombre": nombre, "telefono": digitos}


# Sirve el frontend desde el mismo servidor (carpeta ../frontend)
FRONT = Path(__file__).resolve().parents[2] / "frontend"
if FRONT.is_dir():
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="web")
