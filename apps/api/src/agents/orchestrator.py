"""Orchestration Agent - Main workflow coordinator for Talk2Publish.

This module implements the central orchestration agent using the deepagents
framework. It manages the entire book-writing workflow by coordinating
specialized sub-agents through a stateful LangGraph workflow.

Sub-agents are dynamically loaded from the database, allowing for versioning
and runtime configuration updates.
"""

from typing import Optional
from langgraph.checkpoint.memory import MemorySaver
from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic
import logging

from .loader import load_active_subagents
from ..tools.gap_analysis import gap_analysis
from ..tools.persistence import (
    save_chapter_draft,
    save_chapter_transcript,
    save_hitl_clarifications
)
from ..core.config import settings

logger = logging.getLogger(__name__)


def create_orchestrator():
    """Create and configure the Talk2Publish orchestration agent.

    This function initializes the main deep agent with:
    - Built-in middleware stack (planning, filesystem, sub-agents, summarization, HITL)
    - LangGraph checkpointer for state persistence
    - Sub-agents loaded dynamically from database

    Returns:
        The configured deep agent with checkpointer attached

    Raises:
        RuntimeError: If no active agents found in database
    """
    logger.info("Creating Talk2Publish orchestration agent")

    # Create model with explicit API key from settings
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=settings.anthropic_api_key,
        max_tokens=64000
    )
    logger.info("Configured ChatAnthropic model with API key")

    # Load active sub-agents from database
    try:
        subagents = load_active_subagents()
        if not subagents:
            logger.warning("No active agents found in database")
            raise RuntimeError(
                "No active agents configured. "
                "Please seed the database with agent configurations."
            )
        logger.info("Loaded %d active sub-agents from database", len(subagents))
    except Exception as e:
        logger.error("Failed to load subagents from database: %s", str(e))
        raise

    # Create the main orchestration agent
    orchestrator = create_deep_agent(
        model=model,
        tools=[
            gap_analysis,
            save_chapter_draft,
            save_chapter_transcript,
            save_hitl_clarifications
        ],
        tool_configs={
            "gap_analysis": True  # Enable HITL interrupt for gap analysis
        },
        instructions="""You are the Talk2Publish orchestration agent. Your role is to COORDINATE specialists, not to role-play as them.

**Your ONLY Responsibilities:**
1. Welcome the user and explain the workflow
2. Use the `task` tool to delegate ALL work to specialist sub-agents
3. After sub-agents complete, present their results in structured format
4. Track progress and guide transitions between stages

**CRITICAL RULES:**
- NEVER role-play as a specialist (Biographer, Empath, Title Generator, Planner, Writer)
- ALWAYS use the `task` tool to delegate to sub-agents
- You are a coordinator, not a specialist
- Present sub-agent results using structured labels: **Book Name:**, **Author Name:**, **Theme:**, **Audience Profile:**, **Final Title:**

**Workflow Stages - ALWAYS DELEGATE:**

1. **Book & Author Setup**
   - Use `task` tool to call the "Biographer" sub-agent
   - Instruction: "Collect working title, author name, author bio, and book theme. Ask ONE question at a time."
   - After biographer completes, present results with structured labels

2. **Audience Definition**
   - Announce: "Let me connect you with our Empath specialist..."
   - Use `task` tool to call the "Empath" sub-agent
   - Instruction: "Ask maximum 3 questions ONE AT A TIME to understand the target audience"
   - After empath completes, present results with **Audience Profile:** label

3. **Title Generation**
   - Announce: "Let me bring in our Title Generator specialist..."
   - Use `task` tool to call the "Title Generator" sub-agent
   - Instruction: "Ask if user wants title suggestions. If yes, generate 5 options using book theme and audience profile. If no, use working title."
   - After title generator completes, present results with **Final Title:** label

4. **Book Planning**
   - Announce: "Let me bring in our Planner specialist..."
   - Use `task` tool to call the "Planner" sub-agent
   - Instruction: "Create comprehensive book outline and chapter structure"
   - After planner completes, present outline

5. **Chapter Writing**
   - Announce: "Let me bring in our Writer specialist..."
   - Use `task` tool to call the "Writer" sub-agent
   - Instruction: "Co-create chapter content through interview and iteration"
   - Save approved chapters using persistence tools

**Starting a New Conversation:**
1. Welcome user warmly
2. Explain the workflow briefly
3. IMMEDIATELY use `task` tool to call "Biographer" sub-agent
4. DO NOT ask questions yourself - let the Biographer handle it

**Example First Message:**
"Welcome to Talk2Publish! I'll connect you with specialists to create your book. Let me bring in our Biographer to get started."
[Then IMMEDIATELY call Biographer via task tool]"""
        subagents=subagents
    )

    # Attach checkpointer for state persistence
    # (required for HITL and multi-turn conversations)
    orchestrator.checkpointer = MemorySaver()

    logger.info(
        "Orchestration agent created successfully with %d sub-agents",
        len(subagents)
    )

    return orchestrator


# Global orchestrator instance
_orchestrator: Optional[object] = None


def get_orchestrator():
    """Get or create the global orchestrator instance.

    Returns:
        The orchestration agent instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = create_orchestrator()
    return _orchestrator
