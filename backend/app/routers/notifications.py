from typing import List
from fastapi import APIRouter, HTTPException, status, Query
from app.routers.deps import DBSession, CurrentUser
from app.schemas import NotificationResponse
from app.services import (
    get_user_notifications, mark_notification_as_read, mark_all_notifications_as_read,
    get_notification_by_id, get_unread_notification_count
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_title(notification_type: str) -> str:
    """Generate a user-friendly title based on notification type."""
    titles = {
        "application_received": "New Application",
        "application_accepted": "Application Accepted! 🎉",
        "application_rejected": "Application Update",
        "new_message": "New Message",
        "project_update": "Project Updated",
        "collaborator_joined": "New Team Member",
        "collaborator_left": "Team Update",
        "system": "System Notification",
    }
    return titles.get(notification_type, "Notification")


def build_notification_response(n) -> NotificationResponse:
    notification_type = n.type.value if hasattr(n.type, 'value') else str(n.type)
    project_id = None
    if n.reference_type == "project":
        project_id = n.reference_id
    elif n.reference_type == "application":
        # Could fetch project_id from application if needed
        pass
    
    return NotificationResponse(
        id=n.id,
        user_id=n.user_id,
        type=notification_type,
        reference_type=n.reference_type,
        reference_id=n.reference_id,
        is_read=n.read,
        created_at=n.created_at,
        title=get_notification_title(notification_type),
        message=n.message,
        project_id=project_id
    )


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: CurrentUser,
    db: DBSession,
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    notifications = await get_user_notifications(db, current_user.id, unread_only, skip, limit)
    return [build_notification_response(n) for n in notifications]


@router.get("/count")
async def get_notification_count(current_user: CurrentUser, db: DBSession):
    count = await get_unread_notification_count(db, current_user.id)
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(notification_id: int, current_user: CurrentUser, db: DBSession):
    notification = await get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark your own notifications as read"
        )
    
    notification = await mark_notification_as_read(db, notification)
    return build_notification_response(notification)


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(current_user: CurrentUser, db: DBSession):
    await mark_all_notifications_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}
