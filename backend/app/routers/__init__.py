from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.projects import router as projects_router
from app.routers.applications import router as applications_router
from app.routers.collaborations import router as collaborations_router
from app.routers.conversations import router as conversations_router
from app.routers.notifications import router as notifications_router
from app.routers.reports import router as reports_router

__all__ = [
    "auth_router",
    "profile_router",
    "projects_router",
    "applications_router",
    "collaborations_router",
    "conversations_router",
    "notifications_router",
    "reports_router",
]
