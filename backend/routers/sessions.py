from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import ExamSession
from schemas import SessionCreate, SessionResponse
from auth import verify_google_token
from datetime import datetime

from config import BASE_URL

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    email: str = Depends(verify_google_token),
    db: AsyncSession = Depends(get_db)
):
    if session_data.max_marks not in [50, 100]:
        raise HTTPException(status_code=400, detail="max_marks must be 50 or 100")
        
    if not (10 <= session_data.class_size <= 1000):
        raise HTTPException(status_code=400, detail="class_size must be between 10 and 1000")

    new_session = ExamSession(
        name=session_data.name,
        max_marks=session_data.max_marks,
        class_size=session_data.class_size
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Dynamic URL generation
    base_url = BASE_URL
    
    return SessionResponse(
        id=new_session.id,
        name=new_session.name,
        max_marks=new_session.max_marks,
        class_size=new_session.class_size,
        created_at=new_session.created_at,
        expires_at=new_session.expires_at,
        spots_remaining=new_session.class_size,
        submission_url=f"{base_url}/submit.html?session={new_session.id}",
        dashboard_url=f"{base_url}/dashboard.html?session={new_session.id}"
    )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session_obj = result.scalar_one_or_none()
    
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Session has expired")

    from models import Submission
    count_result = await db.execute(select(Submission).where(Submission.session_id == session_id))
    current_count = len(count_result.scalars().all())

    base_url = BASE_URL
    return SessionResponse(
        id=session_obj.id,
        name=session_obj.name,
        max_marks=session_obj.max_marks,
        class_size=session_obj.class_size,
        created_at=session_obj.created_at,
        expires_at=session_obj.expires_at,
        spots_remaining=session_obj.class_size - current_count,
        submission_url=f"{base_url}/submit.html?session={session_obj.id}",
        dashboard_url=f"{base_url}/dashboard.html?session={session_obj.id}"
    )
