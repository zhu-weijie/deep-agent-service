from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class APIBaseMessage(BaseModel):
    """A message in the chat history."""

    role: Literal["user", "assistant", "tool", "human"]
    content: Any


class InvokeRequest(BaseModel):
    """Request model for the agent invocation endpoint."""

    messages: List[APIBaseMessage]
    files: Optional[Dict[str, str]] = Field(default_factory=dict)
    todos: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class InvokeResponse(BaseModel):
    """Response model for the agent invocation endpoint."""

    messages: List[APIBaseMessage]
    files: Dict[str, str]
    todos: List[Dict[str, Any]]
