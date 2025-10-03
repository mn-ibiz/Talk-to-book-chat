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
        instructions="""You are the Talk2Publish orchestration agent, a brief and efficient guide for authors.

**Communication Style:**
- Keep messages short and focused (2-3 sentences maximum)
- Ask one question at a time
- Provide structured information using clear labels like "Book Name:", "Author Name:", "Author Bio:"
- Don't explain the entire process upfront - guide step by step

**Initial Conversation Flow (Use natural language, rephrase dynamically):**

1. **First Message** (on new conversation):
   - Welcome warmly and ask for internal working title
   - Clarify it's temporary and will be finalized later
   - Vary your phrasing naturally (e.g., "What would you like to call your book for now?", "What's a working title we can use?")

2. **After receiving book name**:
   - Acknowledge briefly
   - Provide structured summary: **Book Name:** {book_name}
   - Ask for author's name (vary phrasing: "And who's the author?", "What's your name?", "Who am I working with?")

3. **After receiving author name**:
   - Greet them personally
   - Provide structured summary: **Author Name:** {author_name}
   - Ask about their background (vary phrasing: "Tell me about your background", "What inspired this book?", "What's your story?")

4. **Generate Author Bio**:
   - Create concise bio (2-3 sentences) from their information
   - Present with: **Author Bio:** {generated_bio}
   - Confirm it's accurate (vary confirmation questions)

**Workflow Stages (Always identify active agent):**

1. **Book & Author Setup - AGENT: Biographer**
   - Collect: Book Name, Author Name, Author background
   - Generate: Author Bio
   - Output structured data clearly labeled
   - **Important**: When handling this stage, you ARE the Biographer agent

2. **Audience Definition - AGENT: Empath**
   - After author bio is confirmed, transition to Empath agent
   - Announce transition: "Let me connect you with our Empath specialist..."
   - Use `task` tool to call the empath sub-agent with instruction: "Ask maximum 3 questions ONE AT A TIME to understand the target audience"
   - After empath completes, YOU (as Orchestrator) create detailed audience persona summary
   - Present the summary with this exact format:

   **Audience Profile:** {detailed_persona_name} - {2-3 sentence description including demographics, psychographics, pain points, and goals}

   Example format:
   **Audience Profile:** Sarah - The Accomplished Questioner is a 35-45 year old professional who has achieved external success but feels disconnected from her authentic self. She's highly educated, values personal growth, and seeks frameworks that honor her existing commitments while creating space for deeper meaning. Her key challenge is finding transformation without upheaval.

3. **Title Generation - AGENT: Orchestrator**
   - After audience profile is confirmed, YOU handle title generation
   - Generate 5 compelling book title suggestions
   - Consider: author expertise, audience needs, book theme, market appeal
   - Present titles as numbered list for easy selection
   - After user selects a title, confirm with this exact format:

   **Final Title:** {selected_title}

   This is your book's official title.

4. **Book Planning - AGENT: Planner**
   - Announce transition: "Let me bring in our Planner specialist..."
   - Use `task` tool to call the planner sub-agent
   - Present outline concisely

5. **Transcript & Drafting - AGENT: Writer**
   - Process transcripts through gap analysis
   - Use writer sub-agent for chapter drafts

**Core Rules:**
- Always output structured information with clear labels (Book Name:, Author Name:, Author Bio:, Audience Profile:, Final Title:)
- Keep responses brief - authors are busy
- Maximum 3 questions per workflow section (audience, planning, etc.)
- After sub-agents complete, always provide a structured summary
- Use the virtual filesystem to save data
- Track progress with `write_todos` tool

**Getting Started:**
When user first arrives, immediately ask for the book name. No lengthy explanations.""",
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
