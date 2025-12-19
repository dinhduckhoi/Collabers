from datetime import datetime
from typing import Optional, List
import re
import bleach
from pydantic import BaseModel, EmailStr, Field, field_validator


def sanitize_html(value: Optional[str]) -> Optional[str]:
    """Strip all HTML tags from a string to prevent XSS."""
    if value is None:
        return None
    return bleach.clean(value, tags=[], strip=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password complexity requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if " " in v:
            raise ValueError("Password must not contain spaces")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    email_verified: bool
    created_at: datetime
    last_active: datetime
    account_status: str

    class Config:
        from_attributes = True


class ProfileLinks(BaseModel):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    other: Optional[str] = None


class ProfileCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    headline: Optional[str] = None
    skills: List[str] = Field(min_length=1)
    roles: Optional[List[str]] = []
    avatar_url: Optional[str] = None
    university: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    bio: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    availability: Optional[str] = None
    hours_per_week: Optional[int] = None
    timezone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    interests: Optional[List[str]] = []
    
    @field_validator("full_name", "headline", "bio", "university", "major", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v):
        return sanitize_html(v)


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    headline: Optional[str] = None
    skills: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    university: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    bio: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    availability: Optional[str] = None
    hours_per_week: Optional[int] = None
    timezone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    links: Optional[ProfileLinks] = None
    interests: Optional[List[str]] = None
    
    @field_validator("full_name", "display_name", "headline", "bio", "university", "major", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v):
        return sanitize_html(v)


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    headline: Optional[str] = None
    avatar_url: Optional[str] = None
    university: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    bio: Optional[str] = None
    skills: List[str] = []
    tech_stack: List[str] = []
    roles: List[str] = []
    preferred_roles: List[str] = []
    availability: Optional[str] = None
    hours_per_week: Optional[int] = None
    timezone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    links: Optional[dict] = None
    interests: List[str] = []
    profile_completeness: int = 0

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    detailed_description: Optional[str] = None
    category: str
    tech_stack: Optional[List[str]] = []
    roles_needed: List[str] = Field(min_length=1)
    commitment_hours: str
    duration: str
    team_size: int = Field(ge=1, le=20)
    visibility: Optional[str] = "public"
    deadline: Optional[datetime] = None
    project_links: Optional[dict] = None
    status: Optional[str] = "draft"
    
    @field_validator("title", "description", "detailed_description", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v):
        return sanitize_html(v)

    @field_validator("category")
    def validate_category(cls, v):
        valid = ["coursework", "hackathon", "startup", "learning", "open_source"]
        if v not in valid:
            raise ValueError(f"category must be one of {valid}")
        return v

    @field_validator("duration")
    def validate_duration(cls, v):
        valid = ["less_than_1_month", "1_to_3_months", "3_to_6_months", "ongoing"]
        if v not in valid:
            raise ValueError(f"duration must be one of {valid}")
        return v

    @field_validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid = ["draft", "open"]
            if v not in valid:
                raise ValueError(f"status must be one of {valid} when creating")
        return v


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    detailed_description: Optional[str] = None
    category: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    roles_needed: Optional[List[str]] = None
    commitment_hours: Optional[str] = None
    duration: Optional[str] = None
    team_size: Optional[int] = Field(None, ge=1, le=20)
    status: Optional[str] = None
    visibility: Optional[str] = None
    deadline: Optional[datetime] = None
    project_links: Optional[dict] = None
    
    @field_validator("title", "description", "detailed_description", mode="before")
    @classmethod
    def sanitize_text_fields(cls, v):
        return sanitize_html(v)

    @field_validator("category")
    def validate_category(cls, v):
        if v is not None:
            valid = ["coursework", "hackathon", "startup", "learning", "open_source"]
            if v not in valid:
                raise ValueError(f"category must be one of {valid}")
        return v

    @field_validator("duration")
    def validate_duration(cls, v):
        if v is not None:
            valid = ["less_than_1_month", "1_to_3_months", "3_to_6_months", "ongoing"]
            if v not in valid:
                raise ValueError(f"duration must be one of {valid}")
        return v

    @field_validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid = ["draft", "open", "in_progress", "filled", "completed", "cancelled"]
            if v not in valid:
                raise ValueError(f"status must be one of {valid}")
        return v


class ProjectResponse(BaseModel):
    id: int
    creator_id: int
    title: str
    description: str
    detailed_description: Optional[str]
    category: str
    tech_stack: List[str]
    roles_needed: List[str]
    commitment_hours: str
    duration: str
    team_size: int
    status: str
    visibility: str
    created_at: datetime
    deadline: Optional[datetime]
    views_count: int
    project_links: Optional[dict]
    creator_profile: Optional[ProfileResponse] = None
    application_count: Optional[int] = None
    team_members: Optional[List["CollaborationResponse"]] = None

    class Config:
        from_attributes = True


class ApplicationCreate(BaseModel):
    project_id: int
    proposed_role: str
    cover_letter: str = Field(min_length=50)


class ApplicationUpdate(BaseModel):
    status: str

    @field_validator("status")
    def validate_status(cls, v):
        valid = ["accepted", "rejected", "withdrawn"]
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    applicant_id: int
    proposed_role: str
    cover_letter: str
    status: str
    created_at: datetime
    responded_at: Optional[datetime]
    applicant_profile: Optional[ProfileResponse] = None
    project: Optional[ProjectResponse] = None

    class Config:
        from_attributes = True


class CollaborationResponse(BaseModel):
    id: int
    project_id: int
    collaborator_id: int
    role: str
    status: str
    joined_at: datetime
    ended_at: Optional[datetime]
    collaborator_profile: Optional[ProfileResponse] = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    created_at: datetime
    read_by: List[int]
    sender_profile: Optional[ProfileResponse] = None

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    project_id: Optional[int]
    participant_ids: List[int]
    type: str
    created_at: datetime
    last_message_at: Optional[datetime]
    messages: Optional[List[MessageResponse]] = None
    project: Optional[ProjectResponse] = None

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    reference_type: str
    reference_id: int
    is_read: bool
    created_at: datetime
    title: str
    message: Optional[str]
    project_id: Optional[int] = None

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    reported_user_id: Optional[int] = None
    reported_project_id: Optional[int] = None
    reason: str
    details: Optional[str] = None

    @field_validator("reason")
    def validate_reason(cls, v):
        valid = ["spam", "harassment", "fake_profile", "inappropriate_content", "other"]
        if v not in valid:
            raise ValueError(f"reason must be one of {valid}")
        return v


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    reported_user_id: Optional[int]
    reported_project_id: Optional[int]
    reason: str
    details: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EmailVerificationRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


ProjectResponse.model_rebuild()
