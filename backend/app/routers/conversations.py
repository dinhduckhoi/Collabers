from typing import List
from fastapi import APIRouter, HTTPException, status, Query
from app.routers.deps import DBSession, CurrentUser
from app.schemas import (
    MessageCreate, MessageResponse, ConversationResponse, ProfileResponse
)
from app.services import (
    get_conversation_by_id, get_user_conversations, get_conversation_messages,
    create_message, mark_messages_as_read, check_user_in_conversation,
    create_notification, get_profile_by_user_id
)
from app.models import NotificationType

router = APIRouter(prefix="/conversations", tags=["Messaging"])


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


def build_message_response(message) -> MessageResponse:
    sender_profile = None
    if message.sender and message.sender.profile:
        sender_profile = build_profile_response(message.sender.profile)
    
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content=message.content,
        created_at=message.created_at,
        read_by=message.read_by or [],
        sender_profile=sender_profile
    )


def build_conversation_response(conversation, messages=None) -> ConversationResponse:
    message_responses = None
    if messages:
        message_responses = [build_message_response(m) for m in messages]
    
    project_data = None
    if conversation.project:
        from app.schemas import ProjectResponse
        project_data = ProjectResponse(
            id=conversation.project.id,
            creator_id=conversation.project.creator_id,
            title=conversation.project.title,
            description=conversation.project.description,
            detailed_description=conversation.project.detailed_description,
            category=conversation.project.category.value,
            tech_stack=conversation.project.tech_stack or [],
            roles_needed=conversation.project.roles_needed or [],
            commitment_hours=conversation.project.commitment_hours,
            duration=conversation.project.duration.value,
            team_size=conversation.project.team_size,
            status=conversation.project.status.value,
            visibility=conversation.project.visibility.value,
            created_at=conversation.project.created_at,
            deadline=conversation.project.deadline,
            views_count=conversation.project.views_count,
            project_links=conversation.project.project_links
        )
    
    return ConversationResponse(
        id=conversation.id,
        project_id=conversation.project_id,
        participant_ids=conversation.participant_ids,
        type=conversation.type.value,
        created_at=conversation.created_at,
        last_message_at=conversation.last_message_at,
        messages=message_responses,
        project=project_data
    )


@router.get("", response_model=List[ConversationResponse])
async def get_my_conversations(current_user: CurrentUser, db: DBSession):
    conversations = await get_user_conversations(db, current_user.id)
    return [build_conversation_response(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: CurrentUser,
    db: DBSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if not await check_user_in_conversation(conversation, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation"
        )
    
    messages = await get_conversation_messages(db, conversation_id, skip, limit)
    await mark_messages_as_read(db, conversation_id, current_user.id)
    
    return build_conversation_response(conversation, messages)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: CurrentUser,
    db: DBSession
):
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if not await check_user_in_conversation(conversation, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation"
        )
    
    message = await create_message(db, conversation_id, current_user.id, data.content)
    
    sender_profile = await get_profile_by_user_id(db, current_user.id)
    sender_name = (sender_profile.full_name or sender_profile.display_name or "Someone") if sender_profile else "Someone"
    
    for participant_id in conversation.participant_ids:
        if participant_id != current_user.id:
            await create_notification(
                db,
                participant_id,
                NotificationType.NEW_MESSAGE,
                "message",
                message.id,
                f"New message from {sender_name}"
            )
    
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content=message.content,
        created_at=message.created_at,
        read_by=message.read_by or [],
        sender_profile=build_profile_response(sender_profile) if sender_profile else None
    )


@router.post("/{conversation_id}/read", status_code=status.HTTP_200_OK)
async def mark_conversation_read(
    conversation_id: int,
    current_user: CurrentUser,
    db: DBSession
):
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if not await check_user_in_conversation(conversation, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation"
        )
    
    await mark_messages_as_read(db, conversation_id, current_user.id)
    return {"message": "Messages marked as read"}
