from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from database import get_db
from models import ExamSession, Submission
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
    if not (10 <= session_data.class_size <= 1000):
        raise HTTPException(status_code=400, detail="class_size must be between 10 and 1000")

    # Determine max_marks from exam_type
    max_marks = 50 if "50" in session_data.exam_type else 100
    
    # Construct unique identifier
    c_id = session_data.class_id.strip() if session_data.class_id else ""
    fac = session_data.faculty_name.strip()
    slot = session_data.slot.strip()
    course = session_data.course_code.strip()
    
    if c_id:
        unique_identifier = f"{c_id}_{fac}_{slot}".upper()
    else:
        unique_identifier = f"{fac}_{slot}_{course}".upper()
        
    session_name = f"{session_data.exam_type} - {unique_identifier}"
    
    # Check for existing session
    existing_res = await db.execute(select(ExamSession).where(ExamSession.unique_identifier == unique_identifier))
    existing_session = existing_res.scalar_one_or_none()
    
    base_url = BASE_URL
    
    if existing_session:
        # Return existing session mapping
        count_res = await db.execute(select(func.count(Submission.id)).where(Submission.session_id == existing_session.id))
        count = count_res.scalar()
        
        return SessionResponse(
            id=existing_session.id,
            name=existing_session.name,
            max_marks=existing_session.max_marks,
            class_size=existing_session.class_size,
            created_at=existing_session.created_at,
            expires_at=existing_session.expires_at,
            spots_remaining=existing_session.class_size - count,
            submission_url=f"{base_url}/submit.html?session={existing_session.id}",
            dashboard_url=f"{base_url}/dashboard.html?session={existing_session.id}"
        )

    # Create new session
    new_session = ExamSession(
        name=session_name,
        max_marks=max_marks,
        class_size=session_data.class_size,
        unique_identifier=unique_identifier
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

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

    # Fix #7: Use SQL COUNT instead of loading all rows into memory
    count_result = await db.execute(select(func.count(Submission.id)).where(Submission.session_id == session_id))
    current_count = count_result.scalar()

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
