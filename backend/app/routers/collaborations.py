from typing import List
from fastapi import APIRouter, HTTPException, status
from app.routers.deps import DBSession, CurrentUser, VerifiedUser
from app.schemas import CollaborationResponse, ProfileResponse, ProjectResponse
from app.services import (
    get_collaboration, get_user_collaborations, get_project_collaborations,
    leave_collaboration, remove_collaborator, get_project_by_id,
    remove_participant_from_conversation, get_or_create_team_conversation
)

router = APIRouter(prefix="/collaborations", tags=["Collaborations"])


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


def build_collaboration_response(collaboration, include_project: bool = False) -> CollaborationResponse:
    collab_profile = None
    if collaboration.collaborator and collaboration.collaborator.profile:
        collab_profile = build_profile_response(collaboration.collaborator.profile)
    
    return CollaborationResponse(
        id=collaboration.id,
        project_id=collaboration.project_id,
        collaborator_id=collaboration.collaborator_id,
        role=collaboration.role,
        status=collaboration.status.value,
        joined_at=collaboration.joined_at,
        ended_at=collaboration.ended_at,
        collaborator_profile=collab_profile
    )


@router.get("/my", response_model=List[CollaborationResponse])
async def get_my_collaborations(current_user: CurrentUser, db: DBSession):
    collaborations = await get_user_collaborations(db, current_user.id)
    return [build_collaboration_response(c) for c in collaborations]


@router.get("/project/{project_id}", response_model=List[CollaborationResponse])
async def get_project_team(project_id: int, db: DBSession):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    collaborations = await get_project_collaborations(db, project_id)
    return [build_collaboration_response(c) for c in collaborations]


@router.post("/{project_id}/leave", status_code=status.HTTP_200_OK)
async def leave_project(project_id: int, current_user: CurrentUser, db: DBSession):
    collaboration = await get_collaboration(db, project_id, current_user.id)
    if not collaboration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a collaborator on this project"
        )
    
    project = await get_project_by_id(db, project_id)
    if project.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project creators cannot leave their own projects"
        )
    
    await leave_collaboration(db, collaboration)
    
    conversation = await get_or_create_team_conversation(db, project_id)
    await remove_participant_from_conversation(db, conversation, current_user.id)
    
    return {"message": "You have left the project"}


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_team_member(
    project_id: int,
    user_id: int,
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
            detail="Only the project creator can remove team members"
        )
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from your own project"
        )
    
    collaboration = await get_collaboration(db, project_id, user_id)
    if not collaboration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a collaborator on this project"
        )
    
    await remove_collaborator(db, collaboration)
    
    conversation = await get_or_create_team_conversation(db, project_id)
    await remove_participant_from_conversation(db, conversation, user_id)
    
    return {"message": "Team member removed"}
