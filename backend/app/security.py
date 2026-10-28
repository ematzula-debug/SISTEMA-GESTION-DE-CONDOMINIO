import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Usuario

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Define SECRET_KEY en el archivo .env")

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    return bool(hashed) and bcrypt.checkpw(password.encode(), hashed.encode())


def make_token(user_id: UUID) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=8)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm="HS256")


def current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if not cred:
        raise HTTPException(401, "Inicia sesión para continuar")
    try:
        uid = jwt.decode(cred.credentials, SECRET_KEY, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "La sesión no es válida o venció")
    user = db.get(Usuario, UUID(uid))
    if not user:
        raise HTTPException(401, "El usuario ya no existe")
    return user


def require(*roles: str):
    def dependencia(user: Usuario = Depends(current_user)) -> Usuario:
        if user.rol not in roles:
            raise HTTPException(403, "No tienes permiso para esta acción")
        return user

    return dependencia
