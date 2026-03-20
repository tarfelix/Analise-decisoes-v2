"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth, analises, ai, dashboard

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed admin user on startup."""
    from app.models import Usuario  # noqa: F401 — ensure all models are imported
    from app.routers.auth import hash_password

    Base.metadata.create_all(bind=engine)

    # Seed admin user if not exists
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == settings.admin_email).first()
        if not admin:
            admin = Usuario(
                email=settings.admin_email,
                nome="Administrador",
                password_hash=hash_password(settings.admin_password),
                role="admin",
                first_access=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Admin user created: %s", settings.admin_email)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.app_name,
    version="3.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(analises.router)
app.include_router(ai.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}
