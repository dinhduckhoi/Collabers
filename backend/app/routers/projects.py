from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from app.routers.deps import DBSession, CurrentUser, VerifiedUser, OptionalUser
from app.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProfileResponse, CollaborationResponse
)
from app.services import (
    create_project, get_project_by_id, update_project, increment_project_views,
    list_projects, get_user_projects, get_profile_by_user_id, check_profile_can_post,
    get_project_collaborations
)

router = APIRouter(prefix="/projects", tags=["Projects"])


def build_profile_response(profile) -> Optional[ProfileResponse]:
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


def build_project_response(project, include_team: bool = False) -> ProjectResponse:
    creator_profile = None
    if project.creator and project.creator.profile:
        creator_profile = build_profile_response(project.creator.profile)
    
    team_members = None
    if include_team and project.collaborations:
        team_members = []
        for collab in project.collaborations:
            if collab.status.value == "active":
                collab_profile = None
                if collab.collaborator and collab.collaborator.profile:
                    collab_profile = build_profile_response(collab.collaborator.profile)
                team_members.append(CollaborationResponse(
                    id=collab.id,
                    project_id=collab.project_id,
                    collaborator_id=collab.collaborator_id,
                    role=collab.role,
                    status=collab.status.value,
                    joined_at=collab.joined_at,
                    ended_at=collab.ended_at,
                    collaborator_profile=collab_profile
                ))
    
    application_count = len(project.applications) if project.applications else 0
    
    return ProjectResponse(
        id=project.id,
        creator_id=project.creator_id,
        title=project.title,
        description=project.description,
        detailed_description=project.detailed_description,
        category=project.category.value,
        tech_stack=project.tech_stack or [],
        roles_needed=project.roles_needed or [],
        commitment_hours=project.commitment_hours,
        duration=project.duration.value,
        team_size=project.team_size,
        status=project.status.value,
        visibility=project.visibility.value,
        created_at=project.created_at,
        deadline=project.deadline,
        views_count=project.views_count,
        project_links=project.project_links,
        creator_profile=creator_profile,
        application_count=application_count,
        team_members=team_members
    )


@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    tech_stack: Optional[str] = None,
    role: Optional[str] = None,
    commitment: Optional[str] = None,
    duration: Optional[str] = None,
    search: Optional[str] = None,
):
    tech_stack_list = tech_stack.split(",") if tech_stack else None
    
    projects = await list_projects(
        db,
        skip=skip,
        limit=limit,
        category=category,
        tech_stack=tech_stack_list,
        role=role,
        commitment=commitment,
        duration=duration,
        search=search
    )
    
    return [build_project_response(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(data: ProjectCreate, current_user: VerifiedUser, db: DBSession):
    profile = await get_profile_by_user_id(db, current_user.id)
    
    if not check_profile_can_post(profile):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete your profile (display name and at least 1 skill) before posting a project"
        )
    
    project = await create_project(db, current_user.id, data.model_dump())
    project = await get_project_by_id(db, project.id)
    
    return build_project_response(project, include_team=True)


@router.get("/my", response_model=List[ProjectResponse])
async def get_my_projects(current_user: CurrentUser, db: DBSession):
    projects = await get_user_projects(db, current_user.id)
    return [build_project_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: DBSession, current_user: OptionalUser = None):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.visibility.value == "unlisted":
        if not current_user or current_user.id != project.creator_id:
            is_collaborator = any(
                c.collaborator_id == current_user.id and c.status.value == "active"
                for c in project.collaborations
            ) if current_user else False
            
            if not is_collaborator:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
    
    await increment_project_views(db, project)
    
    return build_project_response(project, include_team=True)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_existing_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: VerifiedUser,
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
            detail="You can only edit your own projects"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    project = await update_project(db, project, update_data)
    project = await get_project_by_id(db, project.id)
    
    return build_project_response(project, include_team=True)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, current_user: VerifiedUser, db: DBSession):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own projects"
        )
    
    await update_project(db, project, {"status": "cancelled"})
    return None
