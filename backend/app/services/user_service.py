from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Profile, AccountStatus
from app.core.security import get_password_hash, verify_password


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    password_hash = get_password_hash(password)
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def verify_user_email(db: AsyncSession, user: User) -> User:
    user.email_verified = True
    await db.commit()
    await db.refresh(user)
    return user


async def update_last_active(db: AsyncSession, user: User) -> None:
    user.last_active = datetime.now(timezone.utc)
    await db.commit()


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> User:
    user.password_hash = get_password_hash(new_password)
    user.token_version += 1  # Invalidate all existing tokens
    await db.commit()
    await db.refresh(user)
    return user


async def get_profile_by_user_id(db: AsyncSession, user_id: int) -> Optional[Profile]:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def create_profile(db: AsyncSession, user_id: int, data: dict) -> Profile:
    # Remove links if it's a Pydantic model and convert to dict
    links = data.pop("links", None)
    links_dict = links.model_dump() if links and hasattr(links, "model_dump") else (links or {})
    
    profile = Profile(
        user_id=user_id,
        links=links_dict,
        **data
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_profile(db: AsyncSession, profile: Profile, data: dict) -> Profile:
    for key, value in data.items():
        if value is not None:
            if key == "links":
                setattr(profile, key, value.model_dump() if hasattr(value, "model_dump") else value)
            else:
                setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


def check_profile_can_post(profile: Optional[Profile]) -> bool:
    if not profile:
        return False
    if not profile.full_name and not profile.display_name:
        return False
    if not profile.skills or len(profile.skills) == 0:
        return False
    return True
