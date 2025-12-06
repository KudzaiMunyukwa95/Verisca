"""
FastAPI main application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from fastapi.staticfiles import StaticFiles
from app.api.v1 import auth, users, farms, claims, calculations, evidence, sync

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Agricultural Insurance Assessment Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*", # Allow all origins via regex to support random Flutter Web ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files (for uploads)
# Mount Static Files (for uploads)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOADS_DIR), name="static")

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["users"])
app.include_router(farms.router, prefix=f"{settings.API_V1_PREFIX}/farms", tags=["farms"])
app.include_router(claims.router, prefix=f"{settings.API_V1_PREFIX}/claims", tags=["claims"])
app.include_router(calculations.router, prefix=f"{settings.API_V1_PREFIX}/calculations", tags=["calculations"])
app.include_router(evidence.router, prefix=f"{settings.API_V1_PREFIX}/evidence", tags=["evidence"])
app.include_router(sync.router, prefix=f"{settings.API_V1_PREFIX}/sync", tags=["sync"])


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Verisca API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
