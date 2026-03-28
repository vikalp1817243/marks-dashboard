from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from database import engine, AsyncSessionLocal
from models import ExamSession, Submission, ExamScore, CachedStats, PushSubscription

async def cleanup_expired_sessions():
    """Find and delete all data for expired sessions."""
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ExamSession).where(ExamSession.expires_at < datetime.utcnow()))
        expired_sessions = res.scalars().all()
        
        if not expired_sessions:
            return
            
        for session in expired_sessions:
            print(f"Auto-deleting expired session: {session.id}")
            
            await db.delete(session)
            
            # This is slow per session but fine for MVP given low traffic
            subs = await db.execute(select(Submission).where(Submission.session_id == session.id))
            for s in subs.scalars().all(): await db.delete(s)
            
            scores = await db.execute(select(ExamScore).where(ExamScore.session_id == session.id))
            for s in scores.scalars().all(): await db.delete(s)
            
            stats = await db.execute(select(CachedStats).where(CachedStats.session_id == session.id))
            for s in stats.scalars().all(): await db.delete(s)
            
            push_subs = await db.execute(select(PushSubscription).where(PushSubscription.session_id == session.id))
            for p in push_subs.scalars().all(): await db.delete(p)
            
        await db.commit()

# Run every 15 minutes
scheduler = AsyncIOScheduler()
scheduler.add_job(cleanup_expired_sessions, 'interval', minutes=15)
