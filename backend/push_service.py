import json
from pywebpush import webpush, WebPushException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIM_EMAIL
from models import PushSubscription, ExamSession


async def send_push_notifications(session_id: str, db: AsyncSession):
    """Send push notifications to all subscribers of a session at 90% threshold."""
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        print("VAPID keys not configured. Skipping push notifications.")
        return

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

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh_key,
                "auth": sub.auth_key
            }
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=vapid_claims
            )
        except WebPushException as e:
            print(f"Push failed for subscription {sub.id}: {e}")
            # If endpoint is gone (410 or 404), mark for cleanup
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code in (404, 410):
                    stale_ids.append(sub.id)
        except Exception as e:
            print(f"Unexpected push error for subscription {sub.id}: {e}")

    # Clean up stale subscriptions
    if stale_ids:
        for sub_id in stale_ids:
            stale_sub = await db.get(PushSubscription, sub_id)
            if stale_sub:
                await db.delete(stale_sub)
        await db.commit()
        print(f"Cleaned up {len(stale_ids)} stale push subscriptions")

    print(f"Sent push notifications for session {session_id} to {len(subscriptions) - len(stale_ids)} subscribers")
