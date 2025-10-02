"""Chat endpoint for conversational interaction with the orchestration agent."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncIterator
import logging
import uuid
import json

from ..agents.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class Message(BaseModel):
    """Chat message model."""
    role: str
    content: str


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

        # Configure with thread_id for state persistence
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Invoke the orchestrator
        result = orchestrator.invoke(
            {"messages": langgraph_messages},
            config=config
        )

        # Extract response messages
        response_messages = [
            Message(role=msg.get("role", "assistant"), content=msg.get("content", ""))
            for msg in result.get("messages", [])
        ]

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

                # Configure with thread_id
                config = {
                    "configurable": {
                        "thread_id": thread_id
                    }
                }

                # Stream the orchestrator response
                for event in orchestrator.stream(
                    {"messages": langgraph_messages},
                    config=config,
                    stream_mode="values"
                ):
                    # Extract the latest message from event
                    if "messages" in event and event["messages"]:
                        latest_msg = event["messages"][-1]

                        # Format as SSE event
                        event_data = {
                            "type": "message",
                            "role": latest_msg.get("role", "assistant"),
                            "content": latest_msg.get("content", ""),
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
