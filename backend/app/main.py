from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.version)


@app.get("/")
def root() -> dict:
    return {"app": settings.app_name, "docs": "/docs", "health": "/health"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
