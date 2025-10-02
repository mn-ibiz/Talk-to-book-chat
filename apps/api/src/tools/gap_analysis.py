"""Gap Analysis Tool for comparing transcripts with chapter plans.

This tool analyzes the difference between a chapter plan and a raw transcript,
identifying missing topics and new unplanned content.
"""

from typing import Annotated
from langchain_core.tools import tool
from langchain.tools.tool_node import InjectedState
from deepagents.state import FilesystemState
import logging
import json

logger = logging.getLogger(__name__)


@tool
def gap_analysis(
    transcript: str,
    chapter_number: int,
    state: Annotated[FilesystemState, InjectedState],
) -> dict:
    """Analyze gaps between chapter plan and transcript.

    Compares the chapter plan (from virtual filesystem) with the provided
    transcript to identify:
    - Missing topics: key topics from the plan not covered in the transcript
    - New topics: content in the transcript not mentioned in the plan

    Args:
        transcript: The raw text transcript to analyze
        chapter_number: Which chapter this transcript is for
        state: Injected state containing virtual filesystem with chapter plan

    Returns:
        Dict with keys:
        - missing_topics: List of topics from plan not in transcript
        - new_topics: List of topics in transcript not in plan
        - analysis_summary: Brief summary of the gap analysis
    """
    logger.info(f"Starting gap analysis for chapter {chapter_number}")

    # Retrieve chapter plan from virtual filesystem
    files = state.get("files", {})
    chapter_plan_key = f"chapter_{chapter_number}_plan.json"

    if chapter_plan_key not in files:
        logger.error(f"Chapter plan not found: {chapter_plan_key}")
        return {
            "error": f"Chapter plan not found in filesystem: {chapter_plan_key}",
            "missing_topics": [],
            "new_topics": [],
            "analysis_summary": "Error: Chapter plan not available"
        }

    try:
        chapter_plan = json.loads(files[chapter_plan_key])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse chapter plan: {e}")
        return {
            "error": f"Invalid chapter plan JSON: {str(e)}",
            "missing_topics": [],
            "new_topics": [],
            "analysis_summary": "Error: Invalid chapter plan format"
        }

    # Extract key topics from plan
    plan_topics = chapter_plan.get("key_topics", [])
    if not plan_topics:
        logger.warning("No key_topics found in chapter plan")

    # Simple keyword-based gap analysis
    # In production, this would use an LLM for semantic comparison
    missing_topics = []
    for topic in plan_topics:
        # Check if topic appears in transcript (case-insensitive)
        if topic.lower() not in transcript.lower():
            missing_topics.append(topic)
            logger.info(f"Missing topic detected: {topic}")

    # For new topics, we'll rely on HITL questions later
    # This is a placeholder for the MVP
    new_topics = []

    # Store transcript in virtual filesystem for later use
    transcript_key = f"chapter_{chapter_number}_transcript.txt"
    files[transcript_key] = transcript

    # Store gap analysis results
    gap_analysis_key = f"chapter_{chapter_number}_gaps.json"
    gap_data = {
        "missing_topics": missing_topics,
        "new_topics": new_topics,
        "analysis_summary": (
            f"Found {len(missing_topics)} missing topics "
            f"and {len(new_topics)} new topics"
        ),
        "chapter_number": chapter_number
    }
    files[gap_analysis_key] = json.dumps(gap_data, indent=2)

    logger.info(
        f"Gap analysis complete: {len(missing_topics)} missing, "
        f"{len(new_topics)} new"
    )

    return gap_data
