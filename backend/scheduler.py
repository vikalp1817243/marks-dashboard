from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy import delete, text
from datetime import datetime
import httpx

from database import AsyncSessionLocal
from config import BASE_URL
from models import ExamSession, Submission, ExamScore, CachedStats, PushSubscription

async def cleanup_expired_sessions():
    """Find and delete all data for expired sessions.
    
    Fix #6: Uses bulk DELETE WHERE statements instead of loading every row
    into Python and deleting them one-by-one. On TiDB Cloud with ~100ms RTT,
    the old approach of 600 individual DELETEs would take ~60 seconds.
    A single bulk DELETE takes ~100ms regardless of row count.
    """
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ExamSession).where(ExamSession.expires_at < datetime.utcnow()))
        expired_sessions = res.scalars().all()
        
        if not expired_sessions:
            return
            
        for session in expired_sessions:
            sid = session.id
            print(f"Auto-deleting expired session: {sid}")
            
            # Fix #6: Bulk DELETE — one SQL statement per table instead of N
            await db.execute(delete(Submission).where(Submission.session_id == sid))
            await db.execute(delete(ExamScore).where(ExamScore.session_id == sid))
            await db.execute(delete(CachedStats).where(CachedStats.session_id == sid))
            await db.execute(delete(PushSubscription).where(PushSubscription.session_id == sid))
            await db.delete(session)
            
        await db.commit()


async def keep_alive_ping():
    """Prevent BOTH Railway and TiDB from sleeping by generating outbound traffic.
    
    This solves the "double cold start" problem:
    1. Railway sleeps the container after 10 min of no OUTBOUND traffic.
       An HTTP request to our own health endpoint counts as outbound traffic.
    2. TiDB Cloud Serverless hibernates after ~5 min of no connections.
       A lightweight SELECT 1 query keeps the connection pool warm.
    
    Runs every 4 minutes — well under both platforms' sleep thresholds.
    """
    # Ping 1: Hit our own health endpoint (keeps Railway awake via outbound HTTP)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BASE_URL}/api/health")
            print(f"[keep-alive] HTTP ping: {resp.status_code}")
    except Exception as e:
        print(f"[keep-alive] HTTP ping failed: {e}")
    
    # Ping 2: Lightweight DB query (keeps TiDB connection pool warm)
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        print("[keep-alive] DB ping: OK")
    except Exception as e:
        print(f"[keep-alive] DB ping failed: {e}")


# --- Scheduler Setup ---
scheduler = AsyncIOScheduler()
scheduler.add_job(cleanup_expired_sessions, 'interval', minutes=15)
# Keep-alive ping every 4 minutes to prevent Railway sleep (10 min) and TiDB hibernation (~5 min)
scheduler.add_job(keep_alive_ping, 'interval', minutes=4)
