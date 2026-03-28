from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from database import get_db
from models import PushSubscription, ExamSession


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    session_id: str
    endpoint: str
    keys: PushKeys


router = APIRouter(prefix="/api/push", tags=["Push Notifications"])


@router.post("/subscribe")
async def subscribe_push(
    data: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify session exists
    session_res = await db.execute(select(ExamSession).where(ExamSession.id == data.session_id))
    if not session_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if this endpoint is already subscribed for this session
    existing = await db.execute(select(PushSubscription).where(
        PushSubscription.session_id == data.session_id,
        PushSubscription.endpoint == data.endpoint
    ))
    if existing.scalars().first():
        return {"message": "Already subscribed"}

    new_sub = PushSubscription(
        session_id=data.session_id,
        endpoint=data.endpoint,
        p256dh_key=data.keys.p256dh,
        auth_key=data.keys.auth,
        notified=False
    )
    db.add(new_sub)
    await db.commit()

    return {"message": "Subscribed to push notifications"}
