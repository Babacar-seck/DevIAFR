"""
DevIAFR API — FastAPI backend pour le SaaS de production vidéo.

Usage:
    uvicorn main:app --reload --port 8000

Documentation:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import db
from routers import personas, videos

app = FastAPI(
    title="DevIAFR API",
    description="API pour la production de vidéos YouTube automatisées avec personas",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def on_startup():
    db.init_db()

# CORS pour Next.js (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Endpoint de santé pour monitoring."""
    return {"status": "ok", "service": "deviafr-api", "version": "2.0.0"}


@app.get("/")
async def root():
    """Page d'accueil."""
    return {
        "message": "DevIAFR API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "personas": "/api/personas",
            "videos": "/api/videos",
        },
    }


# Inclure les routers
app.include_router(personas.router, prefix="/api/personas", tags=["Personas"])
app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Not found"})


@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
