# app/main.py
from contextlib import asynccontextmanager
import os
from app.core.scheduler import get_scheduler, init_scheduler
from app.core.notify import init_firebase
from app.jobs.appointment_reminders import run_reminders
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings                 # <--- aquí
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.db.init_indexes import ensure_indexes

# routers...
from app.routers import (
    health as health_router,
    auth as auth_router,
    users as users_router,
    patients as patients_router,
    appointments as appointments_router,
    plans as plans_router,
    devices as devices_router,
    google_oauth as google_router,
    me as me_router,
    nutritionist_profile as nutritionist_profile_router,
    recipes as recipes_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo(settings.MONGO_URI, settings.MONGO_DB)
    await ensure_indexes()
    init_firebase()
    init_scheduler()
    sched = get_scheduler()
    sched.add_job(run_reminders, "interval", minutes=1, id="appointment_reminders", replace_existing=True)
    yield
    await close_mongo_connection()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Permitir HTTP solo fuera de prod (para localhost)
if settings.APP_ENV.lower() not in ("prod", "production"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# CORS
cors_origins = list(settings.CORS_ORIGINS or [])
if not cors_origins:
    cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router.router, tags=["health"])
app.include_router(auth_router.router, tags=["auth"])
app.include_router(users_router.router, tags=["users"])
app.include_router(patients_router.router, tags=["patients"])
app.include_router(appointments_router.router, tags=["appointments"])
app.include_router(plans_router.router, tags=["plans"])
app.include_router(devices_router.router)
app.include_router(google_router.router)
app.include_router(me_router.router, tags=["me"])
app.include_router(nutritionist_profile_router.router, tags=["nutritionist_profile"])
app.include_router(recipes_router.router, tags=["recipes"])

os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")

@app.get("/")
async def root():
    return {"ok": True, "service": settings.APP_NAME, "version": settings.APP_VERSION}
