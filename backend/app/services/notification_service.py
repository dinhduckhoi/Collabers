from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    user_id: int,
    notification_type: NotificationType,
    reference_type: str,
    reference_id: int,
    message: Optional[str] = None
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        reference_type=reference_type,
        reference_id=reference_id,
        message=message
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def get_user_notifications(
    db: AsyncSession,
    user_id: int,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50
) -> List[Notification]:
    query = select(Notification).where(Notification.user_id == user_id)
    
    if unread_only:
        query = query.where(Notification.read == False)
    
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def mark_notification_as_read(db: AsyncSession, notification: Notification) -> Notification:
    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_notifications_as_read(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(
        select(Notification)
        .where(
            and_(
                Notification.user_id == user_id,
                Notification.read == False
            )
        )
    )
    notifications = result.scalars().all()
    
    for notification in notifications:
        notification.read = True
    
    await db.commit()


async def get_notification_by_id(db: AsyncSession, notification_id: int) -> Optional[Notification]:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    return result.scalar_one_or_none()


async def get_unread_notification_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(Notification)
        .where(
            and_(
                Notification.user_id == user_id,
                Notification.read == False
            )
        )
    )
    return len(result.scalars().all())
