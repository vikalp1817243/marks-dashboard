from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import datetime

from database import AsyncSessionLocal
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

# Run every 15 minutes
scheduler = AsyncIOScheduler()
scheduler.add_job(cleanup_expired_sessions, 'interval', minutes=15)
