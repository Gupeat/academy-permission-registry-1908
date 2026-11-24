"""FastAPI application for the academy permission registry demo."""
from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.routers.academy import router as academy_router

app = FastAPI(title="Academy Permission Registry", version=__version__)
app.include_router(academy_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"ok": "true", "version": __version__}
