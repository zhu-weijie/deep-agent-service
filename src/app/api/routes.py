from fastapi import APIRouter
import uuid

# Import our API models and the agent service
from app.api.models import InvokeRequest, InvokeResponse, APIBaseMessage
from app.services.agent_service import agent_executor

# Create a new APIRouter instance
router = APIRouter()


@router.post("/invoke", response_model=InvokeResponse, tags=["Agent"])
async def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    """
    Invoke the Deep Agent with a given state and get the final result.
    """
    # Convert APIBaseMessage list to the format LangGraph expects
    messages = [(msg.role, msg.content) for msg in request.messages]

    # Prepare the input for the agent
    agent_input = {
        "messages": messages,
        "files": request.files,
        "todos": request.todos,
    }

    # Add a configurable dictionary with a unique thread_id for each request.
    # This is crucial for managing stateful conversations.
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # Asynchronously invoke the agent with the config
    final_state = await agent_executor.ainvoke(agent_input, config=config)

    # Convert the final state messages back to our API model format
    response_messages = [
        APIBaseMessage(
            role=(
                msg.type if msg.type != "ai" else "assistant"
            ),  # Ensure role is one of the allowed literals
            content=msg.content,
        )
        for msg in final_state["messages"]
    ]

    return InvokeResponse(
        messages=response_messages,
        files=final_state.get("files", {}),
        todos=final_state.get("todos", []),
    )
