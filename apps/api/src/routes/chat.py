"""Chat endpoint for conversational interaction with the orchestration agent."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncIterator
import logging
import uuid
import json
from functools import lru_cache

from ..agents.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@lru_cache(maxsize=128)
def detect_agent_from_content(content: str, default: str = "Orchestrator") -> str:
    """Detect which agent is speaking based on message content patterns.

    Cached to avoid redundant pattern matching on repeated content.
    """
    content_lower = content.lower()

    # Check for explicit agent transitions
    if "empath specialist" in content_lower or "connect you with our empath" in content_lower:
        return "Empath"
    if "planner specialist" in content_lower or "bring in our planner" in content_lower:
        return "Planner"

    # Check for workflow stage keywords
    if any(keyword in content_lower for keyword in ["book name:", "author name:", "author bio:"]):
        if "**author bio:**" in content_lower or "**author name:**" in content_lower:
            return "Biographer"

    if "**audience profile:**" in content_lower:
        return "Orchestrator"  # Orchestrator presents the summary

    if "**final title:**" in content_lower or ("title" in content_lower and any(num in content for num in ["1.", "2.", "3.", "4.", "5."])):
        return "Orchestrator"

    # Check for audience questions (Empath stage)
    if any(q in content_lower for q in ["who is your ideal reader", "target audience", "reader's pain", "reader needs"]):
        return "Empath"

    return default


def extract_text_content(content):
    """Extract text from content blocks if content is a list, otherwise return as-is.

    Optimized for lazy processing - only processes if content is actually a list.
    """
    if not isinstance(content, list):
        return content

    # Fast path: if all items are strings, join directly
    if all(isinstance(block, str) for block in content):
        return "\n".join(content)

    # Process mixed content blocks
    text_parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif isinstance(block, str):
            text_parts.append(block)

    return "\n".join(text_parts)


def calculate_recursion_limit(messages: List[dict]) -> int:
    """Calculate dynamic recursion limit based on conversation stage and complexity.

    Returns:
        int: Recursion limit (30 for simple stages, 100 for complex stages)
    """
    # Check if we're in a complex workflow stage by looking at recent messages
    for msg in reversed(messages[-3:] if len(messages) > 3 else messages):
        content = str(msg.get("content", "")).lower()

        # Complex stages requiring higher recursion limit
        if any(indicator in content for indicator in [
            "empath specialist",
            "planner specialist",
            "task tool",
            "gap analysis",
            "chapter",
            "outline"
        ]):
            return 100  # Complex workflow with sub-agents

    # Simple stages (biographer, title selection)
    if len(messages) <= 3:
        return 30  # Early conversation, simple interactions

    return 50  # Default for moderate complexity


class Message(BaseModel):
    """Chat message model."""
    role: str
    content: str
    agent: Optional[str] = None  # Name of the agent (Biographer, Empath, Planner, etc.)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    messages: List[Message]
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    messages: List[Message]
    thread_id: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the orchestration agent.

    Args:
        request: ChatRequest containing message history and optional thread_id

    Returns:
        ChatResponse with updated messages and thread_id

    Raises:
        HTTPException: If message processing fails
    """
    try:
        # Generate or use existing thread_id for conversation continuity
        thread_id = request.thread_id or str(uuid.uuid4())

        logger.info(f"Processing chat request for thread {thread_id}")

        # Get orchestrator instance
        orchestrator = get_orchestrator()

        # Convert messages to LangGraph format
        langgraph_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        # Configure with thread_id and dynamic recursion limit based on workflow stage
        recursion_limit = calculate_recursion_limit(langgraph_messages)
        config = {
            "configurable": {
                "thread_id": thread_id
            },
            "recursion_limit": recursion_limit  # Dynamic: 30 for simple, 50 for moderate, 100 for complex
        }

        logger.info(f"Using recursion_limit={recursion_limit} for thread {thread_id}")

        # Invoke the orchestrator
        result = orchestrator.invoke(
            {"messages": langgraph_messages},
            config=config
        )

        # Extract response messages - return only NEW assistant messages
        # LangGraph returns full conversation history, but frontend already has user messages
        # Track which messages we've seen by comparing against input count
        all_messages = result.get("messages", [])
        input_count = len(langgraph_messages)

        # Get only messages that came AFTER our input (the AI's new responses)
        # Skip the conversation history and our input message(s)
        new_messages = all_messages[-(len(all_messages) - len(all_messages) + input_count):] if len(all_messages) > input_count else []

        # Actually, simpler approach: return only ASSISTANT messages from the LAST part of conversation
        # This avoids sending back user messages that frontend already has
        response_messages = []

        # Process messages in reverse to get only the newest assistant responses
        seen_user = False
        for msg in reversed(all_messages):
            msg_type = msg.type if hasattr(msg, "type") else msg.get("type", "")

            # Stop when we hit the user message we just sent
            if msg_type in ["human", "user"]:
                if not seen_user:
                    seen_user = True
                    continue
                else:
                    break

            # Only process assistant messages
            if msg_type == "ai" or msg.get("role") == "assistant":
                # Handle both dict format and LangChain message objects
                if hasattr(msg, "type"):
                    # LangChain message object (HumanMessage, AIMessage, etc.)
                    role = "assistant"
                    content = extract_text_content(msg.content)

                    # Extract agent name from message metadata
                    agent_name = None
                    if hasattr(msg, "name") and msg.name:
                        agent_name = msg.name
                    elif hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("agent"):
                        agent_name = msg.additional_kwargs.get("agent")
                else:
                    # Dictionary format (fallback)
                    role = "assistant"
                    content = extract_text_content(msg.get("content", ""))
                    agent_name = msg.get("agent")  # Extract agent from dict format

                # Only add messages with non-empty content
                # (Skip tool-only messages that have no text)
                if content and content.strip():
                    # Use explicit agent name, or detect from content, or default to Orchestrator
                    final_agent = agent_name if agent_name else detect_agent_from_content(content)

                    response_messages.insert(0, Message(  # Insert at beginning to maintain order
                        role=role,
                        content=content,
                        agent=final_agent
                    ))

        logger.info(f"Successfully processed chat for thread {thread_id}")

        return ChatResponse(
            messages=response_messages,
            thread_id=thread_id
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses with support for HITL interrupts.

    This endpoint streams responses and handles Human-in-the-Loop (HITL)
    interrupts for tools configured with tool_configs.

    Args:
        request: ChatRequest containing message history and optional thread_id

    Returns:
        StreamingResponse with Server-Sent Events (SSE) format

    Raises:
        HTTPException: If message processing fails
    """
    try:
        # Generate or use existing thread_id
        thread_id = request.thread_id or str(uuid.uuid4())
        logger.info(f"Starting streaming chat for thread {thread_id}")

        async def event_generator() -> AsyncIterator[str]:
            """Generate SSE events from orchestrator stream."""
            try:
                # Get orchestrator instance
                orchestrator = get_orchestrator()

                # Convert messages to LangGraph format
                langgraph_messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.messages
                ]

                # Configure with thread_id and dynamic recursion limit
                recursion_limit = calculate_recursion_limit(langgraph_messages)
                config = {
                    "configurable": {
                        "thread_id": thread_id
                    },
                    "recursion_limit": recursion_limit  # Dynamic: 30 for simple, 50 for moderate, 100 for complex
                }

                logger.info(f"Streaming with recursion_limit={recursion_limit} for thread {thread_id}")

                # Stream the orchestrator response
                for event in orchestrator.stream(
                    {"messages": langgraph_messages},
                    config=config,
                    stream_mode="values"
                ):
                    # Extract the latest message from event
                    if "messages" in event and event["messages"]:
                        latest_msg = event["messages"][-1]

                        # Handle both LangChain message objects and dictionaries
                        if hasattr(latest_msg, "type"):
                            # LangChain message object
                            msg_type = latest_msg.type
                            role = "assistant" if msg_type == "ai" else "user" if msg_type == "human" else msg_type
                            content = extract_text_content(latest_msg.content)

                            # Extract agent name
                            agent_name = None
                            if hasattr(latest_msg, "name") and latest_msg.name:
                                agent_name = latest_msg.name
                            elif hasattr(latest_msg, "additional_kwargs") and latest_msg.additional_kwargs.get("agent"):
                                agent_name = latest_msg.additional_kwargs.get("agent")

                            # Detect agent from content if not explicitly set
                            if not agent_name and role == "assistant":
                                agent_name = detect_agent_from_content(content)
                        else:
                            # Dictionary format
                            role = latest_msg.get("role", "assistant")
                            content = extract_text_content(latest_msg.get("content", ""))
                            agent_name = latest_msg.get("agent", "Orchestrator")

                        # Only stream assistant messages (skip user messages)
                        if role == "assistant":
                            # Format as SSE event
                            event_data = {
                                "type": "message",
                                "role": role,
                                "content": content,
                                "agent": agent_name or "Orchestrator",
                                "thread_id": thread_id
                            }

                            yield f"data: {json.dumps(event_data)}\n\n"

                # Send completion event
                completion_data = {
                    "type": "done",
                    "thread_id": thread_id
                }
                yield f"data: {json.dumps(completion_data)}\n\n"

            except Exception as e:
                logger.error(f"Error in stream: {str(e)}", exc_info=True)
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        logger.error(f"Error setting up stream: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set up streaming: {str(e)}"
        )
