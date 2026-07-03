'''FastAPI application entry point for the mock MotionTools service.

Runs on port 8001 (agent will run on 8002, keeps them independent).
CORS is permissive here because both v0 UIs and the agent will call it
during development. Tighten for any real deployment.
'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import drivers, bookings, actions, audit, health

app = FastAPI(
    title='Mock MotionTools API',
    description='Standalone functional clone of the MotionTools dispatch '
                'system. Used by the AI rider support agent for looking up '
                'bookings, drivers, and performing operational actions.',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],           # dev only; restrict later
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health.router)
app.include_router(drivers.router)
app.include_router(bookings.router)
app.include_router(actions.router)
app.include_router(audit.router)


@app.on_event("startup")
def seed_if_empty():
    """Auto-seed the database if it's empty. Called by FastAPI on server start.

    This makes deployment self-contained: no manual seed step required.
    On Render's free tier, the disk resets on redeploy so this runs every
    fresh boot, giving the supervisor consistent seeded data every time.
    """
    from app.db.database import SessionLocal, engine, Base
    from app.models.schemas import Booking
    from pathlib import Path
    import subprocess, sys

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        booking_count = session.query(Booking).count()
    if booking_count > 0:
        print(f"[startup] Database already has {booking_count} bookings, skipping seed.")
        return
    print("[startup] Empty database detected. Running seed...")
    script = Path(__file__).resolve().parents[1] / "scripts" / "seed.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("[startup] Seed FAILED:", result.stderr)


@app.get('/', tags=['meta'])
def root():
    return {
        'service': 'mock-motiontools',
        'version': '0.1.0',
        'docs': '/docs',
    }
