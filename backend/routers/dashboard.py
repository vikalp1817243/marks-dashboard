from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import CachedStats, ExamScore, ExamSession
from schemas import CachedStatsResponse
from websocket_manager import manager

router = APIRouter(prefix="/api/sessions", tags=["Dashboard"])

@router.get("/{session_id}/dashboard", response_model=CachedStatsResponse)
async def get_dashboard_stats(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CachedStats).where(CachedStats.session_id == session_id))
    stats = result.scalar_one_or_none()
    
    if not stats:
        # Check if session exists at all
        session_res = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
        if not session_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Return empty stats if no submissions yet
        from datetime import datetime
        return CachedStatsResponse(
            session_id=session_id,
            mean=None, median=None, mode=None, std_dev=None,
            min=None, max=None, q1=None, q3=None,
            count=0, interpretation=None, histogram_json=None,
            updated_at=datetime.utcnow()
        )
        
    return CachedStatsResponse(
        session_id=stats.session_id,
        mean=stats.mean,
        median=stats.median,
        mode=stats.mode,
        std_dev=stats.std_dev,
        min=stats.min,
        max=stats.max,
        q1=stats.q1,
        q3=stats.q3,
        count=stats.count,
        interpretation=stats.interpretation,
        histogram_json=stats.histogram_json,
        updated_at=stats.updated_at
    )

@router.get("/{session_id}/scores")
async def get_raw_scores(session_id: str, db: AsyncSession = Depends(get_db)):
    """Returns an array of anonymous scores for the frontend to render the box plot."""
    result = await db.execute(select(ExamScore.score_value).where(ExamScore.session_id == session_id))
    scores = result.scalars().all()
    return {"scores": [float(score) for score in scores]}

@router.websocket("/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive, listen for any messages if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
