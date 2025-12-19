from typing import List
from fastapi import APIRouter, HTTPException, status
from app.routers.deps import DBSession, CurrentUser, VerifiedUser
from app.schemas import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    ProfileResponse, ProjectResponse, CollaborationResponse
)
from app.services import (
    create_application, get_application_by_id, get_existing_application,
    get_project_applications, get_user_applications, update_application_status,
    mark_application_viewed, get_project_by_id, get_profile_by_user_id,
    check_profile_can_post, create_collaboration, get_or_create_team_conversation,
    add_participant_to_conversation, create_notification
)
from app.models import NotificationType

router = APIRouter(prefix="/applications", tags=["Applications"])


def build_profile_response(profile) -> ProfileResponse:
    if not profile:
        return None
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        display_name=profile.display_name,
        headline=profile.headline,
        avatar_url=profile.avatar_url,
        university=profile.university,
        major=profile.major,
        graduation_year=profile.graduation_year,
        bio=profile.bio,
        skills=profile.skills or [],
        tech_stack=profile.tech_stack or [],
        roles=profile.roles or [],
        preferred_roles=profile.preferred_roles or [],
        availability=profile.availability,
        hours_per_week=profile.hours_per_week,
        timezone=profile.timezone,
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        portfolio_url=profile.portfolio_url,
        links=profile.links or {},
        interests=profile.interests or [],
        profile_completeness=profile.profile_completeness
    )


def build_application_response(application, include_project: bool = False) -> ApplicationResponse:
    applicant_profile = None
    if application.applicant and application.applicant.profile:
        applicant_profile = build_profile_response(application.applicant.profile)
    
    project = None
    if include_project and application.project:
        creator_profile = None
        if application.project.creator and application.project.creator.profile:
            creator_profile = build_profile_response(application.project.creator.profile)
        project = ProjectResponse(
            id=application.project.id,
            creator_id=application.project.creator_id,
            title=application.project.title,
            description=application.project.description,
            detailed_description=application.project.detailed_description,
            category=application.project.category.value,
            tech_stack=application.project.tech_stack or [],
            roles_needed=application.project.roles_needed or [],
            commitment_hours=application.project.commitment_hours,
            duration=application.project.duration.value,
            team_size=application.project.team_size,
            status=application.project.status.value,
            visibility=application.project.visibility.value,
            created_at=application.project.created_at,
            deadline=application.project.deadline,
            views_count=application.project.views_count,
            project_links=application.project.project_links,
            creator_profile=creator_profile
        )
    
    return ApplicationResponse(
        id=application.id,
        project_id=application.project_id,
        applicant_id=application.applicant_id,
        proposed_role=application.proposed_role,
        cover_letter=application.cover_letter,
        status=application.status.value,
        created_at=application.created_at,
        responded_at=application.responded_at,
        applicant_profile=applicant_profile,
        project=project
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_project(data: ApplicationCreate, current_user: VerifiedUser, db: DBSession):
    profile = await get_profile_by_user_id(db, current_user.id)
    if not check_profile_can_post(profile):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete your profile before applying to projects"
        )
    
    project = await get_project_by_id(db, data.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.status.value not in ["open", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This project is not accepting applications"
        )
    
    if project.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot apply to your own project"
        )
    
    existing = await get_existing_application(db, data.project_id, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied to this project"
        )
    
    if data.proposed_role not in project.roles_needed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Available roles: {', '.join(project.roles_needed)}"
        )
    
    application = await create_application(
        db,
        data.project_id,
        current_user.id,
        data.proposed_role,
        data.cover_letter
    )
    
    await create_notification(
        db,
        project.creator_id,
        NotificationType.NEW_APPLICATION,
        "application",
        application.id,
        f"New application from {profile.full_name or profile.display_name} for {project.title}"
    )
    
    application = await get_application_by_id(db, application.id)
    return build_application_response(application, include_project=True)


@router.get("/my", response_model=List[ApplicationResponse])
async def get_my_applications(current_user: CurrentUser, db: DBSession):
    applications = await get_user_applications(db, current_user.id)
    return [build_application_response(app, include_project=True) for app in applications]


@router.get("/project/{project_id}", response_model=List[ApplicationResponse])
async def get_applications_for_project(
    project_id: int,
    current_user: CurrentUser,
    db: DBSession
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view applications for your own projects"
        )
    
    applications = await get_project_applications(db, project_id)
    return [build_application_response(app) for app in applications]


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: int, current_user: CurrentUser, db: DBSession):
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    is_applicant = application.applicant_id == current_user.id
    is_creator = application.project.creator_id == current_user.id
    
    if not is_applicant and not is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this application"
        )
    
    if is_creator and application.status.value == "pending":
        await mark_application_viewed(db, application)
        application = await get_application_by_id(db, application_id)
    
    return build_application_response(application, include_project=True)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    data: ApplicationUpdate,
    current_user: VerifiedUser,
    db: DBSession
):
    application = await get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    is_applicant = application.applicant_id == current_user.id
    is_creator = application.project.creator_id == current_user.id
    
    if data.status == "withdrawn":
        if not is_applicant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the applicant can withdraw an application"
            )
        if application.status.value not in ["pending", "viewed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot withdraw an application that has already been processed"
            )
    elif data.status in ["accepted", "rejected"]:
        if not is_creator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project creator can accept or reject applications"
            )
        if application.status.value not in ["pending", "viewed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This application has already been processed"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status update"
        )
    
    application = await update_application_status(
        db,
        application,
        data.status,
        is_creator=is_creator
    )
    
    if data.status == "accepted":
        collaboration = await create_collaboration(
            db,
            application.project_id,
            application.applicant_id,
            application.proposed_role
        )
        
        conversation = await get_or_create_team_conversation(db, application.project_id)
        await add_participant_to_conversation(db, conversation, application.applicant_id)
        
        await create_notification(
            db,
            application.applicant_id,
            NotificationType.APPLICATION_ACCEPTED,
            "application",
            application.id,
            f"Your application to {application.project.title} has been accepted!"
        )
    elif data.status == "rejected":
        await create_notification(
            db,
            application.applicant_id,
            NotificationType.APPLICATION_REJECTED,
            "application",
            application.id,
            f"Your application to {application.project.title} was declined"
        )
    
    application = await get_application_by_id(db, application_id)
    return build_application_response(application, include_project=True)
