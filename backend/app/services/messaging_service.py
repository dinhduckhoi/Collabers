from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Conversation, Message, ConversationType, User


async def get_conversation_by_id(db: AsyncSession, conversation_id: int) -> Optional[Conversation]:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.project))
        .where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def get_user_conversations(db: AsyncSession, user_id: int) -> List[Conversation]:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.project))
        .order_by(Conversation.last_message_at.desc().nullslast())
    )
    conversations = result.scalars().all()
    return [c for c in conversations if user_id in c.participant_ids]


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[Message]:
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.sender).selectinload(User.profile))
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def create_message(
    db: AsyncSession,
    conversation_id: int,
    sender_id: int,
    content: str
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        read_by=[sender_id]
    )
    db.add(message)
    
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        conversation.last_message_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(message)
    return message


async def mark_messages_as_read(
    db: AsyncSession,
    conversation_id: int,
    user_id: int
) -> None:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
    )
    messages = result.scalars().all()
    
    for message in messages:
        if user_id not in message.read_by:
            message.read_by = message.read_by + [user_id]
    
    await db.commit()


async def check_user_in_conversation(conversation: Conversation, user_id: int) -> bool:
    return user_id in conversation.participant_ids
