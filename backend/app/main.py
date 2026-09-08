from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import diagnostics, incidents, reports
from app.core.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.include_router(diagnostics.router)
app.include_router(incidents.router)
app.include_router(reports.router)


@app.get("/")
def root() -> dict:
    return {"app": settings.app_name, "docs": "/docs", "health": "/health"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
