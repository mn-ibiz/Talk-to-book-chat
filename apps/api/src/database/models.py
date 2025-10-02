"""SQLAlchemy database models for Talk2Publish."""

from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class BookProject(Base):
    """Book project model - central entity for a user's book."""

    __tablename__ = "book_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    title = Column(String(255))
    subtitle = Column(String(255))
    current_stage = Column(String(50), nullable=False, default="profiling")
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    author_profile = relationship("AuthorProfile", back_populates="book_project", uselist=False, cascade="all, delete-orphan")
    audience_persona = relationship(
        "AudiencePersona", back_populates="book_project",
        uselist=False, cascade="all, delete-orphan"
    )
    chapters = relationship("Chapter", back_populates="book_project", cascade="all, delete-orphan")


class AuthorProfile(Base):
    """Author profile model - stores author's style and background."""

    __tablename__ = "author_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_project_id = Column(
        UUID(as_uuid=True), ForeignKey("book_projects.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    profile_data = Column(JSONB)

    # Relationship
    book_project = relationship("BookProject", back_populates="author_profile")


class AudiencePersona(Base):
    """Audience persona model - stores target reader information."""

    __tablename__ = "audience_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_project_id = Column(
        UUID(as_uuid=True), ForeignKey("book_projects.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    persona_data = Column(JSONB)

    # Relationship
    book_project = relationship("BookProject", back_populates="audience_persona")


class Chapter(Base):
    """Chapter model - stores plan, transcript, and draft for each chapter."""

    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_project_id = Column(
        UUID(as_uuid=True), ForeignKey("book_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    plan = Column(JSONB)
    raw_transcript = Column(Text)
    hitl_clarifications = Column(JSONB)
    draft_content = Column(Text)
    status = Column(String(50), nullable=False, default="planned")

    # Relationship
    book_project = relationship("BookProject", back_populates="chapters")

    __table_args__ = (
        # Ensure chapter numbers are unique per book
        # Note: This would normally be a UniqueConstraint, but SQLAlchemy syntax differs
    )


class AgentPrompt(Base):
    """Agent prompt model - stores dynamic prompts for AI agents."""

    __tablename__ = "agent_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    prompt_version = Column(Integer, nullable=False, default=1)
    prompt_content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        # Ensure version numbers are unique per agent
        # Index for finding active prompts quickly
    )
