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


def get_model():
    """Get configured ChatAnthropic model instance."""
    return ChatAnthropic(
        model="claude-sonnet-4-20250514",
        anthropic_api_key=settings.anthropic_api_key,
        max_tokens=64000
    )


class BookAgentState(TypedDict, total=False):
    """State shared across all agents in the book creation workflow."""

    # Current active agent (for UI display and routing)
    active_agent: str

    # Book information
    book_name: str
    author_name: str
    author_bio: str

    # Audience information
    audience_profile: str
    audience_questions_asked: int

    # Title generation
    title_questions_asked: int
    book_genre: str
    key_themes: str
    title_tone: str
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
    Biographer agent - Collects book name, author name, and author bio.

    Workflow:
    1. Greet user and introduce Talk2Publish
    2. Ask for book name
    3. Ask for author name
    4. Ask for author bio
    5. Transition to Empath for audience profiling
    """
    model = get_model()

    # Load biographer config from database
    agent_configs = load_agent_configs()
    biographer_config = agent_configs.get("biographer", {})

    system_prompt = biographer_config.get("prompt", """
You are the Biographer agent for Talk2Publish. Your role is to collect essential information about the book and author.

**Your responsibilities:**
1. Greet the user warmly and introduce the Talk2Publish system
2. Ask for the book name
3. Ask for the author's name
4. Ask for a brief author bio (2-3 sentences)

**Guidelines:**
- Be conversational and friendly
- Ask one question at a time
- Validate that information is provided before moving on
- Once you have all three pieces of information, announce transition to Empath

**When you have all information, say:**
"Great! I have all the book and author details. Let me connect you with our Empath specialist who will help define your target audience."
""")

    # Check what information we have
    has_book_name = bool(state.get("book_name"))
    has_author_name = bool(state.get("author_name"))
    has_author_bio = bool(state.get("author_bio"))

    # If we have all information, transition to Empath
    if has_book_name and has_author_name and has_author_bio:
        transition_message = AIMessage(
            content=f"Perfect! We have:\n- Book: **{state['book_name']}**\n- Author: **{state['author_name']}**\n- Bio: {state['author_bio']}\n\n🔄 Let me connect you with our **Empath specialist** who will help define your target audience."
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
    if not has_book_name and ("book" in last_user_message.lower() or "title" in last_user_message.lower()):
        updates["book_name"] = last_user_message
    elif not has_author_name and ("name" in last_user_message.lower() or "author" in last_user_message.lower()):
        updates["author_name"] = last_user_message
    elif not has_author_bio and ("bio" in last_user_message.lower() or len(last_user_message.split()) > 10):
        updates["author_bio"] = last_user_message

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

    # Load empath config from database
    agent_configs = load_agent_configs()
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
        transition_message = AIMessage(
            content=f"Perfect! Here's your audience profile:\n\n{state['audience_profile']}\n\n🔄 Let me bring in our **Title Generator** to create a compelling book title."
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
    Title Generator agent - Creates compelling book titles through guided questions.

    Workflow:
    1. Ask about book genre/category
    2. Ask about key themes
    3. Ask about desired tone
    4. Generate 5 title options based on collected information
    5. Get user selection and finalize
    6. Transition to Planner
    """
    model = get_model()

    # Load title generator config from database
    agent_configs = load_agent_configs()
    title_config = agent_configs.get("title_generator", {})

    system_prompt = title_config.get("prompt", """
You are the Title Generator for Talk2Publish. Your role is to create compelling book titles.

**Your responsibilities:**
1. Ask 3 questions ONE AT A TIME to understand title requirements:
   - Question 1: "What genre or category best describes your book? (e.g., self-help, business, memoir, technical)"
   - Question 2: "What are the key themes or main topics you want to cover?"
   - Question 3: "What tone would you like for the title? (e.g., inspiring, professional, provocative, practical)"

2. After collecting all answers, generate 5 compelling title options
3. Present titles as a numbered list with brief explanations
4. Get user's selection

**Guidelines:**
- Ask ONE question at a time
- Wait for the user's response before asking the next question
- After all 3 questions, generate exactly 5 title options
- Present titles clearly with numbers for easy selection

**When you have the final title, say:**
"Perfect! Your book title is set. Let me bring in our Planner to structure your book's content."
""")

    # Check what information we have
    title_questions_asked = state.get("title_questions_asked", 0)
    has_genre = bool(state.get("book_genre"))
    has_themes = bool(state.get("key_themes"))
    has_tone = bool(state.get("title_tone"))
    has_final_title = bool(state.get("final_title"))

    # If we have final title, transition to Planner
    if has_final_title:
        transition_message = AIMessage(
            content=f"Excellent! Your book title: **{state['final_title']}**\n\n🔄 Let me bring in our **Planner** to structure your book's content."
        )
        return Command(
            update={
                "messages": [transition_message],
                "active_agent": "Planner",
                "stage": "planner"
            },
            goto="planner"
        )

    # Continue asking questions or generate titles
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

    # Track question progress and extract answers
    if last_user_message and len(last_user_message.split()) > 2:
        if title_questions_asked < 3:
            updates["title_questions_asked"] = title_questions_asked + 1

            # Extract specific answers based on question number
            if not has_genre and title_questions_asked == 0:
                updates["book_genre"] = last_user_message
            elif not has_themes and title_questions_asked == 1:
                updates["key_themes"] = last_user_message
            elif not has_tone and title_questions_asked == 2:
                updates["title_tone"] = last_user_message

    # Check if user selected a title from the options
    if has_genre and has_themes and has_tone:
        if "option" in last_user_message.lower() or any(word in last_user_message.lower() for word in ["choose", "select", "pick", "like"]):
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

    # Load planner config from database
    agent_configs = load_agent_configs()
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
        transition_message = AIMessage(
            content=f"Perfect! Your book plan is finalized.\n\n🔄 Let me bring in our **Writer** to start creating content for your chapters."
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
