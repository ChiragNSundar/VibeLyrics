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
from .routers import sessions, lines, ai, rhymes, journal, stats, user_settings, advanced, scraper, vocabulary, learning, stats_analytics, training, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    import asyncio
    from sqlalchemy import text
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Automatic SQLite migration to add ipa_key column if it doesn't exist
        def check_and_add_ipa_key(connection):
            try:
                res = connection.execute(text("PRAGMA table_info(multisyllabic_words)"))
                columns = [row[1] for row in res.fetchall()]
                if "ipa_key" not in columns:
                    print("[INFO] Adding ipa_key column to multisyllabic_words table...")
                    connection.execute(text("ALTER TABLE multisyllabic_words ADD COLUMN ipa_key VARCHAR(200)"))
                    connection.execute(text("CREATE INDEX ix_multisyllabic_words_ipa_key ON multisyllabic_words (ipa_key)"))
                    print("[OK] Column ipa_key and index added successfully")
            except Exception as e:
                print(f"[WARNING] Migration for ipa_key failed or already applied: {e}")
        
        await conn.run_sync(check_and_add_ipa_key)
        
    print("[OK] Database tables created and migrated")
    
    # Seed database in background
    from .database import async_session
    from .services.rhyme_detector import RhymeDetector
    
    async def run_seeder():
        async with async_session() as session:
            detector = RhymeDetector()
            await detector.seed_phonetic_database(session)
            
            # Incremental migration of null ipa_key values for existing words
            from .models import MultisyllabicWord
            from sqlalchemy import select
            
            has_more = True
            while has_more:
                try:
                    q = select(MultisyllabicWord).where(MultisyllabicWord.ipa_key == None).limit(5000)
                    res = await session.execute(q)
                    words = res.scalars().all()
                    if not words:
                        has_more = False
                        break
                    
                    print(f"[*] Migrating ipa_key for {len(words)} words...")
                    for w in words:
                        w.ipa_key = detector._normalize_to_ipa_key(w.vowel_sequence, w.language)
                    await session.commit()
                except Exception as e:
                    print(f"[WARNING] Background ipa_key migration error: {e}")
                    has_more = False
            
    asyncio.create_task(run_seeder())
    
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
app.include_router(stats_analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(websocket.router, prefix="/api", tags=["WebSockets"])


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
