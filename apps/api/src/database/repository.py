"""Repository pattern implementation for data access layer.

This module provides a clean, business-oriented API for database operations,
abstracting SQLAlchemy details from the agent logic.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from .models import BookProject, AuthorProfile, AudiencePersona, Chapter, AgentPrompt

logger = logging.getLogger(__name__)


class BookProjectRepository:
    """Repository for BookProject operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, user_id: str, **kwargs) -> BookProject:
        """Create a new book project.

        Args:
            user_id: ID of the user creating the project
            **kwargs: Additional project attributes

        Returns:
            BookProject: Created project instance
        """
        project = BookProject(user_id=user_id, **kwargs)
        self.session.add(project)
        logger.info(f"Created book project for user {user_id}")
        return project

    def get_by_id(self, project_id: UUID) -> Optional[BookProject]:
        """Get project by ID."""
        return self.session.query(BookProject).filter(BookProject.id == project_id).first()

    def get_by_user(self, user_id: str) -> List[BookProject]:
        """Get all projects for a user."""
        return self.session.query(BookProject).filter(BookProject.user_id == user_id).all()

    def update_title(self, project_id: UUID, title: str, subtitle: str = None) -> BookProject:
        """Update book title and subtitle.

        Args:
            project_id: Project ID
            title: Book title
            subtitle: Book subtitle (optional)

        Returns:
            BookProject: Updated project
        """
        project = self.get_by_id(project_id)
        if project:
            project.title = title
            if subtitle is not None:
                project.subtitle = subtitle
            logger.info(f"Updated title for project {project_id}")
        return project

    def update_stage(self, project_id: UUID, stage: str) -> BookProject:
        """Update current workflow stage."""
        project = self.get_by_id(project_id)
        if project:
            project.current_stage = stage
            logger.info(f"Updated stage for project {project_id} to {stage}")
        return project


class AuthorProfileRepository:
    """Repository for AuthorProfile operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create_or_update(self, book_project_id: UUID, profile_data: Dict[str, Any]) -> AuthorProfile:
        """Create or update author profile.

        Args:
            book_project_id: Associated book project ID
            profile_data: Profile data as dictionary

        Returns:
            AuthorProfile: Created or updated profile
        """
        profile = self.session.query(AuthorProfile).filter(
            AuthorProfile.book_project_id == book_project_id
        ).first()

        if profile:
            profile.profile_data = profile_data
            logger.info(f"Updated author profile for project {book_project_id}")
        else:
            profile = AuthorProfile(book_project_id=book_project_id, profile_data=profile_data)
            self.session.add(profile)
            logger.info(f"Created author profile for project {book_project_id}")

        return profile

    def get_by_project(self, book_project_id: UUID) -> Optional[AuthorProfile]:
        """Get profile by project ID."""
        return self.session.query(AuthorProfile).filter(
            AuthorProfile.book_project_id == book_project_id
        ).first()


class AudiencePersonaRepository:
    """Repository for AudiencePersona operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create_or_update(self, book_project_id: UUID, persona_data: Dict[str, Any]) -> AudiencePersona:
        """Create or update audience persona.

        Args:
            book_project_id: Associated book project ID
            persona_data: Persona data as dictionary

        Returns:
            AudiencePersona: Created or updated persona
        """
        persona = self.session.query(AudiencePersona).filter(
            AudiencePersona.book_project_id == book_project_id
        ).first()

        if persona:
            persona.persona_data = persona_data
            logger.info(f"Updated audience persona for project {book_project_id}")
        else:
            persona = AudiencePersona(book_project_id=book_project_id, persona_data=persona_data)
            self.session.add(persona)
            logger.info(f"Created audience persona for project {book_project_id}")

        return persona

    def get_by_project(self, book_project_id: UUID) -> Optional[AudiencePersona]:
        """Get persona by project ID."""
        return self.session.query(AudiencePersona).filter(
            AudiencePersona.book_project_id == book_project_id
        ).first()


class ChapterRepository:
    """Repository for Chapter operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create_chapters(self, book_project_id: UUID, chapter_plans: List[Dict[str, Any]]) -> List[Chapter]:
        """Create multiple chapters at once.

        Args:
            book_project_id: Associated book project ID
            chapter_plans: List of chapter data dictionaries

        Returns:
            List[Chapter]: Created chapters
        """
        chapters = []
        for plan in chapter_plans:
            chapter = Chapter(
                book_project_id=book_project_id,
                chapter_number=plan.get("chapter_number"),
                title=plan.get("title"),
                plan=plan.get("plan"),
                status="planned"
            )
            self.session.add(chapter)
            chapters.append(chapter)

        logger.info(f"Created {len(chapters)} chapters for project {book_project_id}")
        return chapters

    def get_by_project(self, book_project_id: UUID) -> List[Chapter]:
        """Get all chapters for a project."""
        return self.session.query(Chapter).filter(
            Chapter.book_project_id == book_project_id
        ).order_by(Chapter.chapter_number).all()

    def get_by_id(self, chapter_id: UUID) -> Optional[Chapter]:
        """Get chapter by ID."""
        return self.session.query(Chapter).filter(Chapter.id == chapter_id).first()

    def update_draft(self, chapter_id: UUID, draft_content: str) -> Chapter:
        """Update chapter draft content.

        Args:
            chapter_id: Chapter ID
            draft_content: Draft content in Markdown

        Returns:
            Chapter: Updated chapter
        """
        chapter = self.get_by_id(chapter_id)
        if chapter:
            chapter.draft_content = draft_content
            chapter.status = "drafted"
            logger.info(f"Updated draft for chapter {chapter_id}")
        return chapter

    def update_transcript(self, chapter_id: UUID, transcript: str) -> Chapter:
        """Update chapter transcript."""
        chapter = self.get_by_id(chapter_id)
        if chapter:
            chapter.raw_transcript = transcript
            chapter.status = "transcript_provided"
            logger.info(f"Updated transcript for chapter {chapter_id}")
        return chapter

    def update_hitl_clarifications(self, chapter_id: UUID, clarifications: Dict[str, Any]) -> Chapter:
        """Update HITL clarifications."""
        chapter = self.get_by_id(chapter_id)
        if chapter:
            chapter.hitl_clarifications = clarifications
            logger.info(f"Updated HITL clarifications for chapter {chapter_id}")
        return chapter


class AgentPromptRepository:
    """Repository for AgentPrompt operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def get_active_agents(self) -> list[AgentPrompt]:
        """Get all active agent prompts.

        Returns:
            List of active AgentPrompt records ordered by agent_name
        """
        return self.session.query(AgentPrompt).filter(
            AgentPrompt.is_active == True  # noqa: E712
        ).order_by(AgentPrompt.agent_name).all()

    def get_active_agent_by_name(self, agent_name: str) -> Optional[AgentPrompt]:
        """Get active agent prompt by name.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentPrompt record if found, None otherwise
        """
        return self.session.query(AgentPrompt).filter(
            AgentPrompt.agent_name == agent_name,
            AgentPrompt.is_active == True  # noqa: E712
        ).first()

    def get_active_prompt(self, agent_name: str) -> Optional[str]:
        """Get active prompt content for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            str: Prompt content if found, None otherwise
        """
        prompt = self.get_active_agent_by_name(agent_name)
        return prompt.prompt_content if prompt else None

    def create_prompt(
        self,
        agent_name: str,
        description: str,
        prompt_content: str,
        version: int = 1,
        is_active: bool = True
    ) -> AgentPrompt:
        """Create a new agent prompt.

        Args:
            agent_name: Name of the agent
            description: Short description of agent's purpose
            prompt_content: The agent's system prompt
            version: Version number of this prompt
            is_active: Whether this prompt should be active

        Returns:
            Created AgentPrompt record
        """
        # Deactivate existing prompts if this one is active
        if is_active:
            self.session.query(AgentPrompt).filter(
                AgentPrompt.agent_name == agent_name
            ).update({"is_active": False})

        prompt = AgentPrompt(
            agent_name=agent_name,
            description=description,
            prompt_version=version,
            prompt_content=prompt_content,
            is_active=is_active
        )
        self.session.add(prompt)
        logger.info(
            f"Created prompt for agent {agent_name}, version {version}"
        )
        return prompt
