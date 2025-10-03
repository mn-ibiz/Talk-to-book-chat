"""Chat endpoint for conversational interaction with the multi-agent system."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncIterator
import logging
import uuid
import json
from functools import lru_cache

from ..agents.multi_agent_system import create_multi_agent_graph

logger = logging.getLogger(__name__)

# Global graph instance (created once and reused)
_graph_instance = None


def get_multi_agent_graph():
    """Get or create the multi-agent graph instance."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_multi_agent_graph()
    return _graph_instance

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

        # Get multi-agent graph instance
        graph = get_multi_agent_graph()

        # Convert messages to LangChain format
        from langchain_core.messages import HumanMessage, AIMessage
        langgraph_messages = []
        for msg in request.messages:
            if msg.role == "user":
                langgraph_messages.append(HumanMessage(content=msg.content))
            else:
                langgraph_messages.append(AIMessage(content=msg.content))

        # Configure with thread_id
        config = {
            "configurable": {
                "thread_id": thread_id
            },
            "recursion_limit": 100
        }

        logger.info(f"Using multi-agent graph for thread {thread_id}")

        # Invoke the multi-agent graph
        result = graph.invoke(
            {"messages": langgraph_messages},
            config=config
        )

        # Extract response messages and active agent from state
        all_messages = result.get("messages", [])
        active_agent = result.get("active_agent", "Biographer")  # Get active agent from state

        # Return only NEW assistant messages (those added after user's input)
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
                # Extract content
                content = extract_text_content(msg.content)

                # Only add messages with non-empty content
                if content and content.strip():
                    response_messages.insert(0, Message(
                        role="assistant",
                        content=content,
                        agent=active_agent  # Use active_agent from state
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
            """Generate SSE events from multi-agent graph stream."""
            try:
                # Get multi-agent graph instance
                graph = get_multi_agent_graph()

                # Convert messages to LangChain format
                from langchain_core.messages import HumanMessage, AIMessage
                langgraph_messages = []
                for msg in request.messages:
                    if msg.role == "user":
                        langgraph_messages.append(HumanMessage(content=msg.content))
                    else:
                        langgraph_messages.append(AIMessage(content=msg.content))

                # Configure with thread_id
                config = {
                    "configurable": {
                        "thread_id": thread_id
                    },
                    "recursion_limit": 100
                }

                logger.info(f"Streaming multi-agent graph for thread {thread_id}")

                # Track previous agent to detect transitions
                previous_agent = None

                # Stream the multi-agent graph response
                # Use stream_mode="updates" to get node-level events
                for event in graph.stream(
                    {"messages": langgraph_messages},
                    config=config,
                    stream_mode="updates"
                ):
                    # Event format: {node_name: {state_updates}}
                    for node_name, state_update in event.items():
                        # Skip human node (waiting for input)
                        if node_name == "human":
                            continue

                        # Get active agent from state update
                        current_agent = state_update.get("active_agent")

                        # Send transition event when agent changes
                        if current_agent and current_agent != previous_agent:
                            transition_data = {
                                "type": "transition",
                                "from_agent": previous_agent or "none",
                                "to_agent": current_agent,
                                "thread_id": thread_id
                            }
                            yield f"data: {json.dumps(transition_data)}\n\n"
                            previous_agent = current_agent

                        # Extract messages from state update
                        if "messages" in state_update and state_update["messages"]:
                            # Get the latest message
                            latest_msg = state_update["messages"][-1]

                            # Only stream AI messages
                            if hasattr(latest_msg, "type") and latest_msg.type == "ai":
                                content = extract_text_content(latest_msg.content)

                                # Format as SSE event
                                event_data = {
                                    "type": "message",
                                    "role": "assistant",
                                    "content": content,
                                    "agent": current_agent or node_name.title(),
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
