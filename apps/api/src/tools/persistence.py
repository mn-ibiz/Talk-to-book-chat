"""Persistence tools for saving artifacts from virtual filesystem to database.

These tools allow the orchestrator to persist data from the virtual filesystem
(state["files"]) to the PostgreSQL database for permanent storage.
"""

from typing import Annotated
from langchain_core.tools import tool
from langchain.tools.tool_node import InjectedState
from deepagents.state import FilesystemState
from uuid import UUID
import logging
import json

from ..database.session import get_session
from ..database.repository import ChapterRepository

logger = logging.getLogger(__name__)


@tool
def save_chapter_draft(
    chapter_id: str,
    chapter_number: int,
    state: Annotated[FilesystemState, InjectedState],
) -> dict:
    """Save chapter draft from virtual filesystem to database.

    Extracts the chapter draft from the virtual filesystem and persists it
    to the database. The draft should be in the file: chapter_X_draft.md

    Args:
        chapter_id: UUID of the chapter to update
        chapter_number: Chapter number (used to locate draft file)
        state: Injected state containing virtual filesystem

    Returns:
        Dict with success status and message
    """
    logger.info(f"Saving draft for chapter {chapter_id}")

    files = state.get("files", {})
    draft_key = f"chapter_{chapter_number}_draft.md"

    if draft_key not in files:
        logger.error(f"Draft file not found: {draft_key}")
        return {
            "success": False,
            "message": f"Draft file not found: {draft_key}",
            "error": "Draft not in virtual filesystem"
        }

    draft_content = files[draft_key]

    try:
        chapter_uuid = UUID(chapter_id)

        with get_session() as session:
            repo = ChapterRepository(session)
            chapter = repo.update_draft(chapter_uuid, draft_content)

            if chapter:
                session.commit()
                logger.info(f"Successfully saved draft for chapter {chapter_id}")
                return {
                    "success": True,
                    "message": f"Draft saved for chapter {chapter_number}",
                    "draft_length": len(draft_content)
                }
            else:
                logger.error(f"Chapter not found: {chapter_id}")
                return {
                    "success": False,
                    "message": f"Chapter not found: {chapter_id}",
                    "error": "Invalid chapter_id"
                }

    except ValueError as e:
        logger.error(f"Invalid UUID: {chapter_id}")
        return {
            "success": False,
            "message": f"Invalid chapter ID format: {chapter_id}",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error saving draft: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to save draft to database",
            "error": str(e)
        }


@tool
def save_chapter_transcript(
    chapter_id: str,
    chapter_number: int,
    state: Annotated[FilesystemState, InjectedState],
) -> dict:
    """Save chapter transcript from virtual filesystem to database.

    Args:
        chapter_id: UUID of the chapter to update
        chapter_number: Chapter number (used to locate transcript file)
        state: Injected state containing virtual filesystem

    Returns:
        Dict with success status and message
    """
    logger.info(f"Saving transcript for chapter {chapter_id}")

    files = state.get("files", {})
    transcript_key = f"chapter_{chapter_number}_transcript.txt"

    if transcript_key not in files:
        logger.error(f"Transcript file not found: {transcript_key}")
        return {
            "success": False,
            "message": f"Transcript file not found: {transcript_key}",
            "error": "Transcript not in virtual filesystem"
        }

    transcript = files[transcript_key]

    try:
        chapter_uuid = UUID(chapter_id)

        with get_session() as session:
            repo = ChapterRepository(session)
            chapter = repo.update_transcript(chapter_uuid, transcript)

            if chapter:
                session.commit()
                logger.info(f"Successfully saved transcript for chapter {chapter_id}")
                return {
                    "success": True,
                    "message": f"Transcript saved for chapter {chapter_number}",
                    "transcript_length": len(transcript)
                }
            else:
                logger.error(f"Chapter not found: {chapter_id}")
                return {
                    "success": False,
                    "message": f"Chapter not found: {chapter_id}",
                    "error": "Invalid chapter_id"
                }

    except ValueError as e:
        logger.error(f"Invalid UUID: {chapter_id}")
        return {
            "success": False,
            "message": f"Invalid chapter ID format: {chapter_id}",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error saving transcript: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to save transcript to database",
            "error": str(e)
        }


@tool
def save_hitl_clarifications(
    chapter_id: str,
    chapter_number: int,
    state: Annotated[FilesystemState, InjectedState],
) -> dict:
    """Save HITL clarifications from virtual filesystem to database.

    Args:
        chapter_id: UUID of the chapter to update
        chapter_number: Chapter number (used to locate clarifications file)
        state: Injected state containing virtual filesystem

    Returns:
        Dict with success status and message
    """
    logger.info(f"Saving HITL clarifications for chapter {chapter_id}")

    files = state.get("files", {})
    clarifications_key = f"chapter_{chapter_number}_clarifications.json"

    if clarifications_key not in files:
        logger.warning(f"No clarifications found: {clarifications_key}")
        return {
            "success": True,
            "message": "No clarifications to save (optional)",
            "clarifications_count": 0
        }

    try:
        clarifications_json = files[clarifications_key]
        clarifications = json.loads(clarifications_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid clarifications JSON: {e}")
        return {
            "success": False,
            "message": "Invalid clarifications format",
            "error": str(e)
        }

    try:
        chapter_uuid = UUID(chapter_id)

        with get_session() as session:
            repo = ChapterRepository(session)
            chapter = repo.update_hitl_clarifications(chapter_uuid, clarifications)

            if chapter:
                session.commit()
                logger.info(f"Successfully saved clarifications for chapter {chapter_id}")
                return {
                    "success": True,
                    "message": f"Clarifications saved for chapter {chapter_number}",
                    "clarifications_count": len(clarifications)
                }
            else:
                logger.error(f"Chapter not found: {chapter_id}")
                return {
                    "success": False,
                    "message": f"Chapter not found: {chapter_id}",
                    "error": "Invalid chapter_id"
                }

    except ValueError as e:
        logger.error(f"Invalid UUID: {chapter_id}")
        return {
            "success": False,
            "message": f"Invalid chapter ID format: {chapter_id}",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error saving clarifications: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to save clarifications to database",
            "error": str(e)
        }
