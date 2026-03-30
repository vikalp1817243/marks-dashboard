import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from database import init_db
from routers import sessions, submit, dashboard, push
from scheduler import scheduler

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # With --workers 4, each worker runs this lifespan independently.
    # We only want ONE worker to run the scheduler (cleanup + keep-alive).
    # Use a process-level flag to ensure only the first worker starts it.
    _scheduler_started = False
    if not scheduler.running:
        scheduler.start()
        _scheduler_started = True
    
    yield
    
    # Shutdown
    if _scheduler_started and scheduler.running:
        scheduler.shutdown()

app = FastAPI(title="Marks Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(submit.router)
app.include_router(dashboard.router)
app.include_router(push.router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/config")
async def get_config():
    from config import GOOGLE_CLIENT_ID, VAPID_PUBLIC_KEY
    return {"google_client_id": GOOGLE_CLIENT_ID, "vapid_public_key": VAPID_PUBLIC_KEY}

# Serve service worker from root (required for push notification scope)
@app.get("/sw.js")
async def serve_sw():
    return FileResponse(str(FRONTEND_DIR / "sw.js"), media_type="application/javascript")

# Serve frontend static assets (CSS, JS)
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

# Serve HTML pages
@app.get("/")
async def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/{page}.html")
async def serve_page(page: str):
    file_path = FRONTEND_DIR / f"{page}.html"
    if file_path.exists():
        return FileResponse(str(file_path))
    return FileResponse(str(FRONTEND_DIR / "index.html"))
