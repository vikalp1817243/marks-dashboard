import json
import asyncio
from pywebpush import webpush, WebPushException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIM_EMAIL
from models import PushSubscription, ExamSession
from database import AsyncSessionLocal


def _send_single_push(subscription_info: dict, payload: str, vapid_claims: dict) -> dict:
    """Synchronous push send — runs in a thread to avoid blocking the event loop.
    
    Fix #4: pywebpush.webpush() uses the synchronous `requests` library internally.
    This helper isolates the blocking HTTP call so it can be offloaded via asyncio.to_thread().
    """
    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=vapid_claims
        )
        return {"status": "ok"}
    except WebPushException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code in (404, 410):
                return {"status": "stale"}
        print(f"Push failed: {e}")
        return {"status": "error"}
    except Exception as e:
        print(f"Unexpected push error: {e}")
        return {"status": "error"}


async def send_push_notifications(session_id: str):
    """Send push notifications to all subscribers of a session at 90% threshold.
    
    Fix #4: This function now creates its OWN database session instead of
    receiving one from the caller. The old code received the request-scoped
    `db` session via asyncio.create_task(), but that session gets closed
    by FastAPI after the request returns — causing race conditions and errors.
    
    Each webpush() call is also offloaded to a thread to prevent blocking
    the async event loop.
    """
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        print("VAPID keys not configured. Skipping push notifications.")
        return

    # Create a dedicated DB session for this background task
    async with AsyncSessionLocal() as db:
        # Fetch session info
        session_res = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
        session_obj = session_res.scalar_one_or_none()

        if not session_obj:
            return

        # Fetch un-notified subscriptions
        subs_res = await db.execute(select(PushSubscription).where(
            PushSubscription.session_id == session_id,
            PushSubscription.notified == False
        ))
        subscriptions = subs_res.scalars().all()

        if not subscriptions:
            return

        # Mark all as notified immediately to prevent duplicate sends
        for sub in subscriptions:
            sub.notified = True
        await db.commit()

        # Build notification payload
        payload = json.dumps({
            "title": f"📊 {session_obj.name} — Dashboard Ready!",
            "body": f"The class has reached 90% submissions. Check the live stats now!",
            "url": f"/dashboard.html?session={session_id}",
            "icon": "/css/icon-192.png"
        })

        vapid_claims = {"sub": VAPID_CLAIM_EMAIL}

        stale_ids = []

        # Send each push in a thread to avoid blocking the event loop
        for sub in subscriptions:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh_key,
                    "auth": sub.auth_key
                }
            }
            result = await asyncio.to_thread(
                _send_single_push, subscription_info, payload, vapid_claims
            )
            if result["status"] == "stale":
                stale_ids.append(sub.id)

        # Clean up stale subscriptions with bulk delete
        if stale_ids:
            for sub_id in stale_ids:
                stale_sub = await db.get(PushSubscription, sub_id)
                if stale_sub:
                    await db.delete(stale_sub)
            await db.commit()
            print(f"Cleaned up {len(stale_ids)} stale push subscriptions")

        print(f"Sent push notifications for session {session_id} to {len(subscriptions) - len(stale_ids)} subscribers")
