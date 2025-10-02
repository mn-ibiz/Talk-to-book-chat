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
import logging

from .loader import load_active_subagents
from ..tools.gap_analysis import gap_analysis
from ..tools.persistence import (
    save_chapter_draft,
    save_chapter_transcript,
    save_hitl_clarifications
)

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
        tools=[
            gap_analysis,
            save_chapter_draft,
            save_chapter_transcript,
            save_hitl_clarifications
        ],
        tool_configs={
            "gap_analysis": True  # Enable HITL interrupt for gap analysis
        },
        instructions="""You are the Talk2Publish orchestration agent, guiding authors \
through the complete book-writing journey.

**Your Workflow Stages:**

1. **Author Profiling (Biographer)**
   - Use `task` tool to call the biographer sub-agent
   - Ensure author_profile.json is saved to virtual filesystem
   - Transition to audience definition

2. **Audience Definition (Empath)**
   - Use `task` tool to call the empath sub-agent
   - Ensure audience_persona.json is saved to virtual filesystem
   - Transition to planning

3. **Book Planning (Planner)**
   - Use `task` tool to call the planner sub-agent for:
     * Title brainstorming
     * Chapter structure
     * Recording prompts
   - Ensure all planning artifacts are saved
   - Present the complete outline to the author

4. **Transcript Ingestion & Gap Analysis**
   - For each chapter:
     * Receive the raw transcript from the user
     * Use the `gap_analysis` tool to compare transcript with chapter plan
     * The tool will identify missing topics and store results in virtual filesystem
     * **Note**: gap_analysis has HITL enabled - you may be interrupted for user review

5. **HITL Clarification** (Human-in-the-Loop)
   - After gap analysis, if there are missing or unclear topics:
     * Generate targeted clarification questions based on gap analysis
     * Ask the user to fill in missing information
     * Capture responses and store in virtual filesystem as `chapter_X_clarifications.json`
     * Ensure all critical gaps are addressed before proceeding to drafting

6. **Chapter Drafting (Writer)**
   - For each chapter (after gap analysis and clarification):
     * Use `task` tool to call the writer sub-agent
     * Writer will read from virtual filesystem:
       - Chapter plan (chapter_X_plan.json)
       - Raw transcript (chapter_X_transcript.txt)
       - Gap analysis results (chapter_X_gaps.json)
       - HITL clarifications (chapter_X_clarifications.json)
     * After writer completes, use persistence tools to save to database:
       - `save_chapter_transcript` - Saves transcript to database
       - `save_hitl_clarifications` - Saves clarifications if any
       - `save_chapter_draft` - Saves final draft to database
     * Provide the chapter_id and chapter_number to each persistence tool

**Core Responsibilities:**
- Guide users through the workflow sequentially
- Use the virtual filesystem to manage session artifacts
- Delegate to specialized sub-agents using the `task` tool
- Track progress using the `write_todos` tool
- Maintain conversation context across multiple turns
- Provide clear next-step guidance to users

**Getting Started:**
When a user first arrives, greet them warmly and explain:
1. What Talk2Publish does
2. The step-by-step process
3. What you need from them to begin
4. Offer to start with author profiling

Remember: You orchestrate, the sub-agents execute. Keep the user informed and engaged!""",
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
