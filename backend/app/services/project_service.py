from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import (
    ProjectPost, Application, Collaboration, User, Profile,
    ProjectStatus, ProjectCategory, ProjectDuration, ProjectVisibility,
    ApplicationStatus, CollaborationStatus, ConversationType, Conversation
)


async def create_project(db: AsyncSession, creator_id: int, data: dict) -> ProjectPost:
    status_str = data.pop("status", "draft")
    status = ProjectStatus(status_str)
    
    category = ProjectCategory(data.pop("category"))
    duration = ProjectDuration(data.pop("duration"))
    visibility_str = data.pop("visibility", "public")
    visibility = ProjectVisibility(visibility_str)
    
    project = ProjectPost(
        creator_id=creator_id,
        status=status,
        category=category,
        duration=duration,
        visibility=visibility,
        **data
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[ProjectPost]:
    result = await db.execute(
        select(ProjectPost)
        .options(selectinload(ProjectPost.creator).selectinload(User.profile))
        .options(selectinload(ProjectPost.collaborations).selectinload(Collaboration.collaborator).selectinload(User.profile))
        .options(selectinload(ProjectPost.applications))
        .where(ProjectPost.id == project_id)
    )
    return result.scalar_one_or_none()


async def update_project(db: AsyncSession, project: ProjectPost, data: dict) -> ProjectPost:
    for key, value in data.items():
        if value is not None:
            if key == "status":
                setattr(project, key, ProjectStatus(value))
            elif key == "category":
                setattr(project, key, ProjectCategory(value))
            elif key == "duration":
                setattr(project, key, ProjectDuration(value))
            elif key == "visibility":
                setattr(project, key, ProjectVisibility(value))
            else:
                setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return project


async def increment_project_views(db: AsyncSession, project: ProjectPost) -> None:
    project.views_count += 1
    await db.commit()


async def list_projects(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    tech_stack: Optional[List[str]] = None,
    role: Optional[str] = None,
    commitment: Optional[str] = None,
    duration: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> List[ProjectPost]:
    query = (
        select(ProjectPost)
        .options(selectinload(ProjectPost.creator).selectinload(User.profile))
        .options(selectinload(ProjectPost.applications))
        .where(ProjectPost.visibility == ProjectVisibility.PUBLIC)
    )
    
    if status:
        query = query.where(ProjectPost.status == ProjectStatus(status))
    else:
        query = query.where(ProjectPost.status == ProjectStatus.OPEN)
    
    if category:
        query = query.where(ProjectPost.category == ProjectCategory(category))
    
    if duration:
        query = query.where(ProjectPost.duration == ProjectDuration(duration))
    
    if commitment:
        query = query.where(ProjectPost.commitment_hours == commitment)
    
    if search:
        # Escape SQL LIKE wildcards to prevent injection
        safe_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_filter = or_(
            ProjectPost.title.ilike(f"%{safe_search}%"),
            ProjectPost.description.ilike(f"%{safe_search}%")
        )
        query = query.where(search_filter)
    
    query = query.order_by(ProjectPost.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    if tech_stack:
        projects = [p for p in projects if any(t in (p.tech_stack or []) for t in tech_stack)]
    
    if role:
        projects = [p for p in projects if role in (p.roles_needed or [])]
    
    return projects


async def get_user_projects(db: AsyncSession, user_id: int) -> List[ProjectPost]:
    result = await db.execute(
        select(ProjectPost)
        .options(selectinload(ProjectPost.creator).selectinload(User.profile))
        .options(selectinload(ProjectPost.applications))
        .options(selectinload(ProjectPost.collaborations).selectinload(Collaboration.collaborator).selectinload(User.profile))
        .where(ProjectPost.creator_id == user_id)
        .order_by(ProjectPost.created_at.desc())
    )
    return result.scalars().all()


async def create_application(
    db: AsyncSession,
    project_id: int,
    applicant_id: int,
    proposed_role: str,
    cover_letter: str
) -> Application:
    application = Application(
        project_id=project_id,
        applicant_id=applicant_id,
        proposed_role=proposed_role,
        cover_letter=cover_letter
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


async def get_application_by_id(db: AsyncSession, application_id: int) -> Optional[Application]:
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.applicant).selectinload(User.profile))
        .options(selectinload(Application.project).selectinload(ProjectPost.creator).selectinload(User.profile))
        .where(Application.id == application_id)
    )
    return result.scalar_one_or_none()


async def get_existing_application(db: AsyncSession, project_id: int, applicant_id: int) -> Optional[Application]:
    result = await db.execute(
        select(Application)
        .where(
            and_(
                Application.project_id == project_id,
                Application.applicant_id == applicant_id,
                Application.status.notin_([ApplicationStatus.WITHDRAWN, ApplicationStatus.REJECTED])
            )
        )
    )
    return result.scalar_one_or_none()


async def get_project_applications(db: AsyncSession, project_id: int) -> List[Application]:
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.applicant).selectinload(User.profile))
        .where(Application.project_id == project_id)
        .order_by(Application.created_at.desc())
    )
    return result.scalars().all()


async def get_user_applications(db: AsyncSession, user_id: int) -> List[Application]:
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.applicant).selectinload(User.profile))
        .options(selectinload(Application.project).selectinload(ProjectPost.creator).selectinload(User.profile))
        .where(Application.applicant_id == user_id)
        .order_by(Application.created_at.desc())
    )
    return result.scalars().all()


async def update_application_status(
    db: AsyncSession,
    application: Application,
    status: str,
    is_creator: bool = False
) -> Application:
    new_status = ApplicationStatus(status)
    
    if not is_creator and status == "withdrawn":
        application.status = new_status
    elif is_creator and status in ["accepted", "rejected"]:
        application.status = new_status
        application.responded_at = datetime.now(timezone.utc)
    else:
        raise ValueError("Invalid status update")
    
    await db.commit()
    await db.refresh(application)
    return application


async def mark_application_viewed(db: AsyncSession, application: Application) -> Application:
    if application.status == ApplicationStatus.PENDING:
        application.status = ApplicationStatus.VIEWED
        await db.commit()
        await db.refresh(application)
    return application


async def create_collaboration(
    db: AsyncSession,
    project_id: int,
    collaborator_id: int,
    role: str
) -> Collaboration:
    collaboration = Collaboration(
        project_id=project_id,
        collaborator_id=collaborator_id,
        role=role
    )
    db.add(collaboration)
    await db.commit()
    await db.refresh(collaboration)
    return collaboration


async def get_collaboration(db: AsyncSession, project_id: int, collaborator_id: int) -> Optional[Collaboration]:
    result = await db.execute(
        select(Collaboration)
        .where(
            and_(
                Collaboration.project_id == project_id,
                Collaboration.collaborator_id == collaborator_id,
                Collaboration.status == CollaborationStatus.ACTIVE
            )
        )
    )
    return result.scalar_one_or_none()


async def get_project_collaborations(db: AsyncSession, project_id: int) -> List[Collaboration]:
    result = await db.execute(
        select(Collaboration)
        .options(selectinload(Collaboration.collaborator).selectinload(User.profile))
        .where(
            and_(
                Collaboration.project_id == project_id,
                Collaboration.status == CollaborationStatus.ACTIVE
            )
        )
    )
    return result.scalars().all()


async def get_user_collaborations(db: AsyncSession, user_id: int) -> List[Collaboration]:
    result = await db.execute(
        select(Collaboration)
        .options(selectinload(Collaboration.project).selectinload(ProjectPost.creator).selectinload(User.profile))
        .options(selectinload(Collaboration.collaborator).selectinload(User.profile))
        .where(
            and_(
                Collaboration.collaborator_id == user_id,
                Collaboration.status == CollaborationStatus.ACTIVE
            )
        )
    )
    return result.scalars().all()


async def leave_collaboration(db: AsyncSession, collaboration: Collaboration) -> Collaboration:
    collaboration.status = CollaborationStatus.LEFT
    collaboration.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(collaboration)
    return collaboration


async def remove_collaborator(db: AsyncSession, collaboration: Collaboration) -> Collaboration:
    collaboration.status = CollaborationStatus.REMOVED
    collaboration.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(collaboration)
    return collaboration


async def get_or_create_team_conversation(db: AsyncSession, project_id: int) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(
            and_(
                Conversation.project_id == project_id,
                Conversation.type == ConversationType.TEAM_CHAT
            )
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        project = await get_project_by_id(db, project_id)
        if not project:
            raise ValueError("Project not found")
        
        conversation = Conversation(
            project_id=project_id,
            participant_ids=[project.creator_id],
            type=ConversationType.TEAM_CHAT
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    
    return conversation


async def add_participant_to_conversation(
    db: AsyncSession,
    conversation: Conversation,
    user_id: int
) -> Conversation:
    if user_id not in conversation.participant_ids:
        conversation.participant_ids = conversation.participant_ids + [user_id]
        await db.commit()
        await db.refresh(conversation)
    return conversation


async def remove_participant_from_conversation(
    db: AsyncSession,
    conversation: Conversation,
    user_id: int
) -> Conversation:
    if user_id in conversation.participant_ids:
        conversation.participant_ids = [p for p in conversation.participant_ids if p != user_id]
        await db.commit()
        await db.refresh(conversation)
    return conversation
