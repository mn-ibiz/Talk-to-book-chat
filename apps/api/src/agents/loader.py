"""Agent loader service - Dynamically loads agent configurations from database.

This module provides functionality to load active agent configurations from the
database and transform them into deepagents SubAgent format.
"""

from typing import List
from deepagents.types import SubAgent
from ..database.repository import AgentPromptRepository
from ..database.session import get_session
import logging

logger = logging.getLogger(__name__)


def load_active_subagents() -> List[SubAgent]:
    """Load all active subagent configurations from the database.

    Queries the agent_prompts table for all active agents and transforms
    them into the SubAgent TypedDict format required by deepagents.

    Returns:
        List of SubAgent configuration dictionaries

    Raises:
        Exception: If database query fails
    """
    logger.info("Loading active subagents from database")

    with get_session() as session:
        repo = AgentPromptRepository(session)
        active_prompts = repo.get_active_agents()

        subagents: List[SubAgent] = []
        for prompt in active_prompts:
            subagent: SubAgent = {
                "name": prompt.agent_name,
                "description": prompt.description,
                "prompt": prompt.prompt_content,
                # tools, model, middleware inherit from parent by default
            }
            subagents.append(subagent)
            logger.debug(
                "Loaded agent: %s (v%d)",
                prompt.agent_name,
                prompt.prompt_version
            )

        logger.info("Loaded %d active subagents", len(subagents))
        return subagents


def load_subagent_by_name(agent_name: str) -> SubAgent:
    """Load a specific active subagent configuration by name.

    Args:
        agent_name: The name of the agent to load

    Returns:
        SubAgent configuration dictionary

    Raises:
        ValueError: If no active agent found with the given name
    """
    logger.info("Loading subagent: %s", agent_name)

    with get_session() as session:
        repo = AgentPromptRepository(session)
        prompt = repo.get_active_agent_by_name(agent_name)

        if prompt is None:
            raise ValueError(f"No active agent found with name: {agent_name}")

        subagent: SubAgent = {
            "name": prompt.agent_name,
            "description": prompt.description,
            "prompt": prompt.prompt_content,
        }

        logger.debug(
            "Loaded agent: %s (v%d)",
            prompt.agent_name,
            prompt.prompt_version
        )
        return subagent
