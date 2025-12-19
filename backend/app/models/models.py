import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum,
    JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class AccountStatus(enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class Availability(enum.Enum):
    ACTIVELY_LOOKING = "actively_looking"
    OPEN_TO_OFFERS = "open_to_offers"
    NOT_AVAILABLE = "not_available"


class ProjectCategory(enum.Enum):
    COURSEWORK = "coursework"
    HACKATHON = "hackathon"
    STARTUP = "startup"
    LEARNING = "learning"
    OPEN_SOURCE = "open_source"


class ProjectDuration(enum.Enum):
    LESS_THAN_1_MONTH = "less_than_1_month"
    ONE_TO_3_MONTHS = "1_to_3_months"
    THREE_TO_6_MONTHS = "3_to_6_months"
    ONGOING = "ongoing"


class ProjectStatus(enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FILLED = "filled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectVisibility(enum.Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"


class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class CollaborationStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    LEFT = "left"
    REMOVED = "removed"


class ConversationType(enum.Enum):
    APPLICATION_DISCUSSION = "application_discussion"
    TEAM_CHAT = "team_chat"
    DIRECT = "direct"


class NotificationType(enum.Enum):
    NEW_APPLICATION = "new_application"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"
    NEW_MESSAGE = "new_message"
    PROJECT_UPDATE = "project_update"


class ReportReason(enum.Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    FAKE_PROFILE = "fake_profile"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    OTHER = "other"


class ReportStatus(enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0)  # Increment to invalidate all tokens
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    account_status: Mapped[AccountStatus] = mapped_column(SQLEnum(AccountStatus), default=AccountStatus.ACTIVE)
    
    profile: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="user", uselist=False)
    projects: Mapped[List["ProjectPost"]] = relationship("ProjectPost", back_populates="creator")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="applicant")
    collaborations: Mapped[List["Collaboration"]] = relationship("Collaboration", back_populates="collaborator")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")
    sent_messages: Mapped[List["Message"]] = relationship("Message", back_populates="sender")
    reports_filed: Mapped[List["Report"]] = relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")


class Profile(Base):
    __tablename__ = "profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    display_name: Mapped[Optional[str]] = mapped_column(String(100))  # Keep for backwards compat
    headline: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    university: Mapped[Optional[str]] = mapped_column(String(200))
    major: Mapped[Optional[str]] = mapped_column(String(200))
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    skills: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    tech_stack: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    roles: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    preferred_roles: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)  # Keep for backwards compat
    availability: Mapped[Optional[str]] = mapped_column(String(50))
    hours_per_week: Mapped[Optional[int]] = mapped_column(Integer)
    timezone: Mapped[Optional[str]] = mapped_column(String(50))
    github_url: Mapped[Optional[str]] = mapped_column(String(500))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500))
    links: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # Keep for backwards compat
    interests: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    user: Mapped["User"] = relationship("User", back_populates="profile")
    
    @property
    def profile_completeness(self) -> int:
        fields = [
            self.full_name or self.display_name,
            self.skills and len(self.skills) > 0,
            self.university,
            self.major,
            self.graduation_year,
            self.bio,
            self.tech_stack and len(self.tech_stack) > 0,
            self.roles and len(self.roles) > 0,
            self.availability,
            self.hours_per_week,
            self.github_url or self.linkedin_url or self.portfolio_url,
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)


class ProjectPost(Base):
    __tablename__ = "project_posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[ProjectCategory] = mapped_column(SQLEnum(ProjectCategory), nullable=False)
    tech_stack: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    roles_needed: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    commitment_hours: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[ProjectDuration] = mapped_column(SQLEnum(ProjectDuration), nullable=False)
    team_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    visibility: Mapped[ProjectVisibility] = mapped_column(SQLEnum(ProjectVisibility), default=ProjectVisibility.PUBLIC)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    project_links: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    creator: Mapped["User"] = relationship("User", back_populates="projects")
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="project")
    collaborations: Mapped[List["Collaboration"]] = relationship("Collaboration", back_populates="project")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="project")
    
    __table_args__ = (
        Index("ix_project_posts_status", "status"),
        Index("ix_project_posts_category", "category"),
    )


class Application(Base):
    __tablename__ = "applications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project_posts.id"), nullable=False)
    applicant_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    proposed_role: Mapped[str] = mapped_column(String(50), nullable=False)
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    project: Mapped["ProjectPost"] = relationship("ProjectPost", back_populates="applications")
    applicant: Mapped["User"] = relationship("User", back_populates="applications")
    
    __table_args__ = (
        UniqueConstraint("project_id", "applicant_id", name="uq_application_project_applicant"),
        Index("ix_applications_status", "status"),
    )


class Collaboration(Base):
    __tablename__ = "collaborations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("project_posts.id"), nullable=False)
    collaborator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[CollaborationStatus] = mapped_column(SQLEnum(CollaborationStatus), default=CollaborationStatus.ACTIVE)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    project: Mapped["ProjectPost"] = relationship("ProjectPost", back_populates="collaborations")
    collaborator: Mapped["User"] = relationship("User", back_populates="collaborations")
    
    __table_args__ = (
        UniqueConstraint("project_id", "collaborator_id", name="uq_collaboration_project_collaborator"),
    )


class Conversation(Base):
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("project_posts.id"))
    participant_ids: Mapped[List[int]] = mapped_column(JSON, nullable=False)
    type: Mapped[ConversationType] = mapped_column(SQLEnum(ConversationType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    project: Mapped[Optional["ProjectPost"]] = relationship("ProjectPost", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_by: Mapped[List[int]] = mapped_column(JSON, default=list)
    
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")


class Notification(Base):
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    message: Mapped[Optional[str]] = mapped_column(String(500))
    
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read"),
    )


class Report(Base):
    __tablename__ = "reports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reporter_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    reported_project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("project_posts.id"))
    reason: Mapped[ReportReason] = mapped_column(SQLEnum(ReportReason), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    reporter: Mapped["User"] = relationship("User", back_populates="reports_filed", foreign_keys=[reporter_id])
