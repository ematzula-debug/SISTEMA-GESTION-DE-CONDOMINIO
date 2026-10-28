# Sistema de Gestión de Condominio

- `backend/`: API en Python (FastAPI) con PostgreSQL.
- `frontend/`: la interfaz web (HTML, CSS y JavaScript). El backend la sirve por sí mismo.

## Puesta en marcha
Necesitas Python 3.10 o superior y PostgreSQL en ejecución.

1. Crea la base de datos: `createdb condominio` (o desde pgAdmin).
2. Entra a la carpeta del backend e instala las dependencias:
   ```
   cd backend
   python -m venv .venv
   source .venv/bin/activate        # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copia `.env.example` como `.env` y completa `DATABASE_URL` (usuario y clave de PostgreSQL) y `SECRET_KEY`.
   Para generar la clave: `python -c "import secrets; print(secrets.token_hex(32))"`
4. Crea tablas y datos iniciales: `python seed.py` (te pide la contraseña del administrador `admin@condominio.com`).
5. Inicia el sistema: `uvicorn app.main:app --reload`
6. Abre http://localhost:8000 e inicia sesión. La documentación de la API está en http://localhost:8000/docs

## Qué ve cada rol
| Rol | Módulos | Puede modificar |
|-----|---------|-----------------|
| Administrador | Todos | Todo |
| Guardia | Viviendas, Visitas, Mantenimiento | Visitas y Mantenimiento |
| Propietario / Inquilino | Mi vivienda, Pagos, Visitas, Mantenimiento, Reportes (solo lo de su vivienda) | Solo crear solicitudes de mantenimiento para su vivienda |

## Crear el acceso de un propietario
1. Entra como administrador y crea la vivienda en **Viviendas**.
2. En **Usuarios**, crea al propietario con rol `Propietario`, su correo, **la vivienda asignada** y una contraseña de al menos 8 caracteres.
3. Al iniciar sesión, esa persona solo verá los pagos, visitas y solicitudes de esa vivienda. Un residente sin vivienda asignada no ve ningún dato.

## Antes de publicarlo en internet
- Usa HTTPS y una `SECRET_KEY` larga y secreta.
- Si el frontend se aloja en otro dominio, escribe su dirección en `CORS_ORIGINS` (`.env`) y la del backend en `API_URL` (`frontend/index.html`).
- Las tablas se crean automáticamente; para cambios futuros del esquema conviene usar migraciones (Alembic).

## Botón de WhatsApp
Propietarios, inquilinos y guardias ven un botón verde de WhatsApp en todas las pantallas. Al pulsarlo se abre WhatsApp con un mensaje que ya incluye su nombre, rol y vivienda.

El número al que escriben es el **teléfono del usuario Administrador**: entra como administrador, edita su usuario en **Usuarios** y escribe el número en **Teléfono**. Si prefieres otro número, ponlo en `WHATSAPP_NUMERO` dentro de `backend/.env` y reinicia el servidor.

## Publicar en línea (GitHub, Supabase y Render)
El backend sirve también el frontend, así que en Render se crea **un solo servicio web**.

1. **GitHub:** sube la carpeta `condominio` completa (con `backend/` y `frontend/` dentro del repositorio). Nunca subas el archivo `.env`.
2. **Supabase:** crea un proyecto, entra a **Connect** y copia la dirección **Session pooler** (puerto 5432). La conexión directa solo usa IPv6 y Render no puede alcanzarla. Reemplaza `[YOUR-PASSWORD]` por la contraseña de la base.
3. **Tablas y administrador:** pon esa dirección como `DATABASE_URL` en `backend/.env` y corre `python seed.py` desde tu computadora.
4. **Render:** crea un *Web Service* con el repositorio de GitHub.
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Variables de entorno: `DATABASE_URL` (la del Session pooler), `SECRET_KEY` (clave larga), `PYTHON_VERSION` = `3.12.8`
   - Health Check Path: `/api/salud`
5. Abre la dirección `https://....onrender.com` e inicia sesión como administrador.

Si no puedes correr `seed.py`, agrega en Render la variable `ADMIN_PASSWORD` (mínimo 8 caracteres): al arrancar crea el administrador si todavía no existe.
