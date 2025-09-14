from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .db.mongo import connect_to_mongo, close_mongo_connection
from .db.init_indexes import ensure_indexes
from .routers import auth, users, health

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.on_event("startup")
    async def startup():
        await connect_to_mongo()
        await ensure_indexes()

    @app.on_event("shutdown")
    async def shutdown():
        await close_mongo_connection()

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)

    return app

app = create_app()
