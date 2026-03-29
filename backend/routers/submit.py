from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from database import get_db
from models import ExamSession, Submission, ExamScore
from schemas import ScoreSubmit
from auth import verify_google_token, hash_email
from datetime import datetime
from stats import recalculate_stats
from websocket_manager import manager
import asyncio
from push_service import send_push_notifications

router = APIRouter(prefix="/api/sessions", tags=["Submit"])

@router.post("/{session_id}/submit")
async def submit_score(
    session_id: str,
    score_data: ScoreSubmit,
    email: str = Depends(verify_google_token),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve session
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session_obj = result.scalar_one_or_none()
    
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Session has expired")
        
    # Validate score
    if score_data.score > session_obj.max_marks or score_data.score < 0:
        raise HTTPException(status_code=400, detail=f"Score must be between 0 and {session_obj.max_marks}")

    # Check capacity BEFORE inserting
    sub_count_res = await db.execute(select(func.count(Submission.id)).where(Submission.session_id == session_id))
    current_count = sub_count_res.scalar()
    
    if current_count >= session_obj.class_size:
        raise HTTPException(status_code=403, detail="Class size capacity reached.")
        
    hashed_id = hash_email(email, session_id)
    
    # Check duplicate
    dup_check = await db.execute(select(Submission).where(
        Submission.session_id == session_id,
        Submission.hashed_student_id == hashed_id
    ))
    if dup_check.scalars().first():
        raise HTTPException(status_code=409, detail="You have already submitted your marks for this session.")
        
    # Atomic transaction
    new_sub = Submission(session_id=session_id, hashed_student_id=hashed_id)
    new_score = ExamScore(session_id=session_id, score_value=round(score_data.score, 3))
    
    db.add(new_sub)
    db.add(new_score)
    await db.commit()
    
    # Recalculate stats
    new_stats_model = await recalculate_stats(session_id, db)
    
    # Trigger 90% push notification in background
    # Fix #4: No longer passes the request-scoped db session — push_service creates its own
    new_count = current_count + 1
    if new_count >= 0.9 * session_obj.class_size:
        asyncio.create_task(send_push_notifications(session_id))

    # WebSocket Broadcast
    if new_stats_model:
        await manager.broadcast_stats(session_id, new_stats_model)

    return {"message": "Score submitted successfully anonymously."}

