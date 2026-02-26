"""
VibeLyrics FastAPI Backend
Main application entry point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import settings
from .database import engine, Base
from .routers import sessions, lines, ai, rhymes, journal, stats, user_settings, advanced, scraper, vocabulary, learning


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database tables created")
    
    yield
    
    # Cleanup
    await engine.dispose()


app = FastAPI(
    title="VibeLyrics API",
    description="AI-powered lyric writing assistant",
    version="2.4.0",
    lifespan=lifespan
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio uploads
os.makedirs("uploads/audio", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(lines.router, prefix="/api", tags=["Lines"])
app.include_router(ai.router, prefix="/api", tags=["AI"])
app.include_router(rhymes.router, prefix="/api", tags=["Rhymes"])
app.include_router(journal.router, prefix="/api/journal", tags=["Journal"])
app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])
app.include_router(user_settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(advanced.router, prefix="/api", tags=["Advanced"])
app.include_router(scraper.router, prefix="/api/scraper", tags=["Scraper"])
app.include_router(vocabulary.router, prefix="/api/vocabulary", tags=["Vocabulary"])
app.include_router(learning.router, prefix="/api", tags=["Learning"])


@app.get("/")
async def root():
    return {
        "name": "VibeLyrics API",
        "version": "2.4.0",
        "docs": "/docs",
        "status": "running"
    }

# Serve frontend in production (if built)
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
