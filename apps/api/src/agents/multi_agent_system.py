"""
Multi-Agent System for Talk2Publish

This module implements a LangGraph-based multi-agent system where each specialist
(Biographer, Empath, Title Generator, Planner, Writer) is a graph node that can
communicate directly with the user and transition smoothly between agents.

Key improvements over task-tool architecture:
- Each agent is a graph node (not a subagent)
- Direct agent-to-user communication (no relaying)
- State-based agent tracking (not pattern matching)
- Smooth transitions with full context retention
- Real-time transition events for UI updates
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import operator

from ..tools.gap_analysis import gap_analysis
from ..tools.persistence import save_chapter_draft, save_chapter_transcript, save_hitl_clarifications
from .loader import load_agent_configs
from ..core.config import settings

# Global cached instances for performance
_model_instance = None
_agent_configs_cache = None


def get_model():
    """Get cached ChatAnthropic model instance (created once, reused for performance)."""
    global _model_instance
    if _model_instance is None:
        _model_instance = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=64000
        )
    return _model_instance


def get_agent_configs():
    """Get cached agent configurations (loaded once from DB, reused for performance)."""
    global _agent_configs_cache
    if _agent_configs_cache is None:
        _agent_configs_cache = load_agent_configs()
    return _agent_configs_cache


class BookAgentState(TypedDict, total=False):
    """State shared across all agents in the book creation workflow."""

    # Current active agent (for UI display and routing)
    active_agent: str

    # Book information (collected by Biographer)
    book_name: str  # Working/internal title
    author_name: str
    author_bio: str
    book_theme: str  # Key topics/themes - collected early in workflow

    # Audience information (collected by Empath)
    audience_profile: str
    audience_questions_asked: int

    # Title generation
    wants_title_suggestions: bool  # Whether user wants title suggestions
    final_title: str

    # Planning
    book_plan: str

    # Conversation history
    messages: Annotated[list, operator.add]

    # Current workflow stage
    stage: Literal["biographer", "empath", "title_generator", "planner", "writer", "complete"]

    # Human-in-the-loop flag
    waiting_for_user: bool


def biographer_node(state: BookAgentState) -> Command[Literal["empath", END]]:
    """
    Biographer agent - Collects book name, author details, and book theme.

    Workflow:
    1. Greet user and introduce Talk2Publish
    2. Ask for internal/working book name
    3. Ask for author name
    4. Ask for author bio
    5. Ask for book theme (key topics)
    6. Transition to Empath for audience profiling
    """
    model = get_model()

    # Get cached biographer config (faster than DB lookup)
    agent_configs = get_agent_configs()
    biographer_config = agent_configs.get("biographer", {})

    system_prompt = biographer_config.get("prompt", """
You are the Biographer agent for Talk2Publish. Your role is to collect essential information about the book and author.

**Your responsibilities:**
1. Greet the user warmly and introduce the Talk2Publish system
2. Ask for the internal/working book name (explain this is temporary and will be refined later)
3. Ask for the author's name
4. Ask for a brief author bio (2-3 sentences)
5. Ask for the book theme (what key topics or themes will the book cover?)

**Guidelines:**
- Be conversational and friendly
- Ask ONE question at a time
- Validate that information is provided before moving on
- Once you have all FOUR pieces of information, announce transition to Empath

**When you have all information, say:**
"Perfect! I have all the essential details. Let me connect you with our Empath specialist who will help define your target audience."
""")

    # Check what information we have
    has_book_name = bool(state.get("book_name"))
    has_author_name = bool(state.get("author_name"))
    has_author_bio = bool(state.get("author_bio"))
    has_book_theme = bool(state.get("book_theme"))

    # If we have all information, transition to Empath
    if has_book_name and has_author_name and has_author_bio and has_book_theme:
        # Fast transition with minimal message
        transition_message = AIMessage(
            content=f"🔄 Connecting with **Empath specialist** for audience profiling..."
        )
        return Command(
            update={
                "messages": [transition_message],
                "active_agent": "Empath",
                "stage": "empath"
            },
            goto="empath"
        )

    # Otherwise, continue collecting information
    # Build messages list with system message + conversation history
    from langchain_core.messages import SystemMessage
    messages_for_model = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = model.invoke(messages_for_model)

    # Extract information from conversation
    last_user_message = next((m.content for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), "")

    updates = {
        "messages": [response],
        "active_agent": "Biographer",
        "stage": "biographer"
    }

    # Simple extraction logic (can be enhanced with structured output)
    if not has_book_name and len(last_user_message.split()) > 0:
        updates["book_name"] = last_user_message
    elif not has_author_name and has_book_name and len(last_user_message.split()) > 0:
        updates["author_name"] = last_user_message
    elif not has_author_bio and has_author_name and len(last_user_message.split()) > 5:
        updates["author_bio"] = last_user_message
    elif not has_book_theme and has_author_bio and len(last_user_message.split()) > 3:
        updates["book_theme"] = last_user_message

    # Return and wait for next user message (END means wait for resume)
    return Command(update=updates, goto=END)


def empath_node(state: BookAgentState) -> Command[Literal["title_generator", END]]:
    """
    Empath agent - Defines target audience through multi-turn conversation.

    Workflow:
    1. Introduce audience profiling process
    2. Ask maximum 3 questions ONE AT A TIME:
       - Who is the primary audience?
       - What problems do they face?
       - What transformation do they seek?
    3. Synthesize audience profile
    4. Transition to Title Generator
    """
    model = get_model()

    # Get cached empath config (faster than DB lookup)
    agent_configs = get_agent_configs()
    empath_config = agent_configs.get("empath", {})

    system_prompt = empath_config.get("prompt", """
You are the Empath agent for Talk2Publish. Your role is to deeply understand the target audience.

**Your responsibilities:**
1. Ask insightful questions about the target audience (maximum 3 questions, ONE AT A TIME)
2. Understand reader pain points, aspirations, and transformation goals
3. Synthesize a comprehensive audience profile

**Question sequence:**
- Question 1: "Who is the primary audience for this book? (demographics, profession, life stage)"
- Question 2: "What specific problems or challenges does this audience face?"
- Question 3: "What transformation or outcome do readers hope to achieve?"

**Guidelines:**
- Ask ONE question at a time
- Wait for the user's response before asking the next question
- Be empathetic and curious
- Once you have answers to all questions, create a synthesized audience profile

**When you have the complete profile, say:**
"Excellent! I have a clear picture of your audience. Let me bring in our Title Generator to create a compelling book title."
""")

    # Count how many audience questions have been answered
    audience_questions_asked = state.get("audience_questions_asked", 0)
    has_audience_profile = bool(state.get("audience_profile"))

    # If we have complete audience profile, transition to Title Generator
    if has_audience_profile:
        # Fast transition with minimal message
        transition_message = AIMessage(
            content=f"🔄 Connecting with **Title Generator**..."
        )
        return Command(
            update={
                "messages": [transition_message],
                "active_agent": "Title Generator",
                "stage": "title_generator"
            },
            goto="title_generator"
        )

    # Continue audience profiling
    from langchain_core.messages import SystemMessage
    messages_for_model = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = model.invoke(messages_for_model)

    updates = {
        "messages": [response],
        "active_agent": "Empath",
        "stage": "empath"
    }

    # Check if we've collected enough information (3 questions answered)
    last_user_message = next((m.content for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), "")

    if audience_questions_asked < 3 and len(last_user_message.split()) > 5:
        updates["audience_questions_asked"] = audience_questions_asked + 1

        # If we've asked 3 questions, synthesize the profile
        if updates["audience_questions_asked"] >= 3:
            # Extract all user responses about audience
            audience_responses = [
                m.content for m in state.get("messages", [])[-6:]  # Last 3 Q&A pairs
                if isinstance(m, HumanMessage)
            ]
            updates["audience_profile"] = " | ".join(audience_responses)

    # Wait for more user input
    return Command(update=updates, goto=END)


def title_generator_node(state: BookAgentState) -> Command[Literal["planner", END]]:
    """
    Title Generator agent - Creates compelling book titles using collected information.

    Workflow:
    1. Ask if user wants title suggestions
    2. If yes, generate 5 title options using book_theme and audience_profile
    3. Get user selection and finalize
    4. Transition to Planner
    """
    model = get_model()

    # Get cached title generator config (faster than DB lookup)
    agent_configs = get_agent_configs()
    title_config = agent_configs.get("title_generator", {})

    system_prompt = title_config.get("prompt", """
You are the Title Generator for Talk2Publish. Your role is to create compelling book titles.

**Your responsibilities:**
1. First, ask the user if they would like title suggestions for their book
2. If they say yes, generate 5 compelling title options based on:
   - The book theme they provided earlier
   - The target audience profile
   - The author's background and expertise
3. Present titles as a numbered list (1-5) with brief explanations
4. Get user's selection from the options

**Guidelines:**
- Start by asking: "Would you like me to suggest some title options for your book?"
- If yes, generate exactly 5 professional title options
- Present titles clearly with numbers for easy selection
- Each title should resonate with the target audience
- If they say no, you can transition to Planner

**When you have the final title, say:**
"Perfect! Your book title is set. Let me bring in our Planner to create your book outline and chapter structure."
""")

    # Check what information we have
    wants_title_suggestions = state.get("wants_title_suggestions")
    has_final_title = bool(state.get("final_title"))

    # If we have final title, transition to Planner
    if has_final_title:
        # Fast transition with minimal message
        transition_message = AIMessage(
            content=f"🔄 Connecting with **Planner** for book structure..."
        )
        return Command(
            update={
                "messages": [transition_message],
                "active_agent": "Planner",
                "stage": "planner"
            },
            goto="planner"
        )

    # If user doesn't want title suggestions, use working title and transition to Planner
    if wants_title_suggestions is False:
        working_title = state.get("book_name", "Untitled")
        # Fast transition with minimal message
        transition_message = AIMessage(
            content=f"🔄 Connecting with **Planner** for book structure..."
        )
        return Command(
            update={
                "messages": [transition_message],
                "active_agent": "Planner",
                "stage": "planner",
                "final_title": working_title
            },
            goto="planner"
        )

    # Continue with title generation workflow
    from langchain_core.messages import SystemMessage
    messages_for_model = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = model.invoke(messages_for_model)

    updates = {
        "messages": [response],
        "active_agent": "Title Generator",
        "stage": "title_generator"
    }

    # Extract information from last user message
    last_user_message = next((m.content for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), "")

    # Check if user wants title suggestions (if not already set)
    if wants_title_suggestions is None and last_user_message:
        last_lower = last_user_message.lower()
        if any(word in last_lower for word in ["yes", "yeah", "sure", "ok", "okay", "please", "would like"]):
            updates["wants_title_suggestions"] = True
        elif any(word in last_lower for word in ["no", "nope", "not", "don't"]):
            updates["wants_title_suggestions"] = False

    # Check if user selected a title from the options
    if wants_title_suggestions is True and last_user_message:
        # Look for selection keywords or option numbers
        if any(word in last_user_message.lower() for word in ["option", "choose", "select", "pick", "like", "prefer"]) or \
           any(char.isdigit() for char in last_user_message):
            updates["final_title"] = last_user_message

    return Command(update=updates, goto=END)


def planner_node(state: BookAgentState) -> Command[Literal["writer", END]]:
    """
    Planner agent - Creates comprehensive book structure and chapter outlines.

    Workflow:
    1. Review book title, author, and audience
    2. Create book structure (parts, chapters)
    3. Develop chapter outlines
    4. Get user approval
    5. Transition to Writer for content creation
    """
    model = get_model()

    # Get cached planner config (faster than DB lookup)
    agent_configs = get_agent_configs()
    planner_config = agent_configs.get("planner", {})

    system_prompt = planner_config.get("prompt", """
You are the Planner agent for Talk2Publish. Your role is to structure the book's content.

**Your responsibilities:**
1. Analyze the book title, author background, and target audience
2. Create a comprehensive book structure (parts and chapters)
3. Develop detailed chapter outlines
4. Get user feedback and approval
5. Finalize the book plan

**Book structure should include:**
- Number of parts/sections
- Chapter titles and summaries
- Key concepts for each chapter
- Logical progression and flow

**When the plan is approved, say:**
"Great! Your book plan is finalized. Let me bring in our Writer to start creating content."
""")

    has_book_plan = bool(state.get("book_plan"))

    # If we have approved book plan, transition to Writer
    if has_book_plan:
        # Fast transition with minimal message
        transition_message = AIMessage(
            content=f"🔄 Connecting with **Writer** for content creation..."
        )
        return Command(
            update={
                "messages": [transition_message],
                "active_agent": "Writer",
                "stage": "writer"
            },
            goto="writer"
        )

    # Create book plan
    from langchain_core.messages import SystemMessage
    messages_for_model = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = model.invoke(messages_for_model)

    updates = {
        "messages": [response],
        "active_agent": "Planner",
        "stage": "planner"
    }

    # Check if user approved the plan
    last_user_message = next((m.content for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), "")
    if "approve" in last_user_message.lower() or "looks good" in last_user_message.lower() or "yes" in last_user_message.lower():
        # Extract the book plan from recent AI messages
        plan_message = next((m.content for m in reversed(state.get("messages", [])) if isinstance(m, AIMessage) and len(m.content) > 100), "")
        updates["book_plan"] = plan_message

    return Command(update=updates, goto=END)


def writer_node(state: BookAgentState) -> Command[Literal[END]]:
    """
    Writer agent - Creates chapter content through iterative co-writing.

    Workflow:
    1. Select next chapter to work on
    2. Conduct interview about chapter topic
    3. Generate chapter draft
    4. Get feedback and iterate
    5. Save approved chapters
    """
    model = get_model()

    system_prompt = """
You are the Writer agent for Talk2Publish. Your role is to co-create book chapters.

**Your responsibilities:**
1. Select the next chapter to work on
2. Interview the author about the chapter topic
3. Generate chapter drafts based on the conversation
4. Iterate based on feedback

**Guidelines:**
- Be collaborative and creative
- Ask probing questions to extract the author's knowledge
- Generate content that matches the author's voice
- Iterate until the chapter meets quality standards

Note: Chapter saving tools will be re-enabled in a future update.
"""

    # Tool calling removed temporarily - will be re-implemented with proper execution loop
    from langchain_core.messages import SystemMessage
    messages_for_model = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = model.invoke(messages_for_model)

    updates = {
        "messages": [response],
        "active_agent": "Writer",
        "stage": "writer"
    }

    # Check if book is complete
    last_user_message = next((m.content for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)), "")
    if "complete" in last_user_message.lower() or "finished" in last_user_message.lower():
        updates["stage"] = "complete"

    return Command(update=updates, goto=END)


def create_multi_agent_graph() -> StateGraph:
    """
    Creates the multi-agent graph for Talk2Publish.

    Graph structure:
    - Entry point determined by 'stage' field in state
    - Each agent processes messages and either:
      1. Returns END to wait for next user message
      2. Uses Command(goto="next_agent") to transition

    Workflow stages:
    - biographer → empath → title_generator → planner → writer → END

    Returns:
        StateGraph: Compiled graph with MemorySaver checkpointer
    """
    # Create the graph
    workflow = StateGraph(BookAgentState)

    # Add nodes
    workflow.add_node("biographer", biographer_node)
    workflow.add_node("empath", empath_node)
    workflow.add_node("title_generator", title_generator_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("writer", writer_node)

    # Set conditional entry point based on current stage
    def route_entry(state: BookAgentState) -> str:
        """Route to the appropriate agent based on current stage."""
        stage = state.get("stage", "biographer")
        return stage

    workflow.set_conditional_entry_point(route_entry, {
        "biographer": "biographer",
        "empath": "empath",
        "title_generator": "title_generator",
        "planner": "planner",
        "writer": "writer",
        "complete": END
    })

    # Compile graph with checkpointer
    graph = workflow.compile(checkpointer=MemorySaver())

    return graph
