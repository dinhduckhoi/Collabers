import os
import uuid
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from app.routers.deps import DBSession, CurrentUser, VerifiedUser
from app.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from app.services import get_profile_by_user_id, create_profile, update_profile

router = APIRouter(prefix="/profile", tags=["Profile"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "avatars")
UPLOAD_DIR = os.path.realpath(UPLOAD_DIR)  # Normalize for path traversal checks
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Magic bytes for image validation
IMAGE_SIGNATURES = {
    b'\xff\xd8\xff': 'jpeg',
    b'\x89PNG\r\n\x1a\n': 'png',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',  # WebP starts with RIFF
}


def detect_image_type(content: bytes) -> str | None:
    """Detect image type by checking magic bytes."""
    for signature, img_type in IMAGE_SIGNATURES.items():
        if content.startswith(signature):
            return img_type
    # WebP has RIFF at start, then WEBP at offset 8
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return 'webp'
    return None


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: CurrentUser, db: DBSession):
    profile = await get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create your profile first."
        )
    
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


@router.post("/me", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_my_profile(data: ProfileCreate, current_user: CurrentUser, db: DBSession):
    existing_profile = await get_profile_by_user_id(db, current_user.id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PATCH to update."
        )
    
    profile = await create_profile(db, current_user.id, data.model_dump())
    
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


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(data: ProfileUpdate, current_user: CurrentUser, db: DBSession):
    profile = await get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create your profile first."
        )
    
    update_data = data.model_dump(exclude_unset=True)
    profile = await update_profile(db, profile, update_data)
    
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


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_user_profile(user_id: int, db: DBSession):
    profile = await get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
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


@router.post("/me/avatar", response_model=ProfileResponse)
async def upload_avatar(
    current_user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...)
):
    """Upload avatar image for the current user's profile."""
    profile = await get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create your profile first."
        )
    
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Validate file content (magic bytes) - prevents uploading malicious files with fake extensions
    image_type = detect_image_type(content)
    if image_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file content. File does not appear to be a valid image."
        )
    
    # Delete old avatar if exists
    if profile.avatar_url and profile.avatar_url.startswith("/api/profile/avatars/"):
        old_filename = profile.avatar_url.split("/")[-1]
        old_path = os.path.join(UPLOAD_DIR, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)
    
    # Save new avatar
    filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Update profile with new avatar URL
    avatar_url = f"/api/profile/avatars/{filename}"
    profile = await update_profile(db, profile, {"avatar_url": avatar_url})
    
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


@router.get("/avatars/{filename}")
async def get_avatar(filename: str):
    """Serve avatar image with path traversal protection."""
    # Prevent path traversal attacks - only use the basename
    safe_filename = os.path.basename(filename)
    
    # Reject any attempt to use directory traversal
    if safe_filename != filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    filepath = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Double-check the resolved path is within UPLOAD_DIR
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(UPLOAD_DIR):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found"
        )
    return FileResponse(filepath)
