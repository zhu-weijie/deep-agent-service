import json
import uuid
from typing import Any, get_args

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import BaseMessage

from app.api.models import APIBaseMessage, InvokeRequest, InvokeResponse
from app.services.agent_service import agent_executor

router = APIRouter()


def convert_event_data_to_json_serializable(data: Any) -> Any:
    """
    Recursively converts event data to a JSON-serializable format.
    Handles complex objects like LangChain's BaseMessage and internal objects.
    """
    if isinstance(data, dict):
        return {
            key: convert_event_data_to_json_serializable(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [convert_event_data_to_json_serializable(item) for item in data]
    elif isinstance(data, BaseMessage):
        role = getattr(data, "type", "unknown")
        if role == "ai":
            role = "assistant"

        allowed_roles = get_args(APIBaseMessage.model_fields["role"].annotation)
        content = convert_event_data_to_json_serializable(data.content)

        if role in allowed_roles:
            return APIBaseMessage(role=role, content=content).dict()
        else:
            return {"role": role, "content": content}

    # ** THE FIX IS HERE **
    # Final fallback for any other non-serializable object types.
    try:
        # Check if the object is serializable by trying to dump it
        json.dumps(data)
        return data
    except TypeError:
        # If it's not serializable, convert it to a string representation
        return str(data)


async def stream_generator(request: InvokeRequest):
    """
    Generator function that streams agent events.
    """
    messages = [(msg.role, msg.content) for msg in request.messages]
    agent_input = {
        "messages": messages,
        "files": request.files,
        "todos": request.todos,
    }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    async for event in agent_executor.astream_events(
        agent_input, config=config, version="v1"
    ):
        # This check is important to filter out internal heartbeat events if any
        if event["event"] != "ping":
            serializable_data = convert_event_data_to_json_serializable(event["data"])
            yield f"event: {event['event']}\ndata: {json.dumps(serializable_data)}\n\n"


@router.post("/stream", tags=["Agent"])
async def stream_agent(request: InvokeRequest):
    """
    Invoke the Deep Agent and stream back events as they happen.
    """
    return StreamingResponse(stream_generator(request), media_type="text/event-stream")


@router.post("/invoke", response_model=InvokeResponse, tags=["Agent"])
async def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    messages = [(msg.role, msg.content) for msg in request.messages]
    agent_input = {
        "messages": messages,
        "files": request.files,
        "todos": request.todos,
    }
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    final_state = await agent_executor.ainvoke(agent_input, config=config)
    response_messages = [
        APIBaseMessage(
            role=msg.type if msg.type != "ai" else "assistant", content=msg.content
        )
        for msg in final_state["messages"]
    ]
    return InvokeResponse(
        messages=response_messages,
        files=final_state.get("files", {}),
        todos=final_state.get("todos", []),
    )
