"""Research Tools.

This module provides search and content processing utilities for the research agent,
including web search capabilities and content summarization tools.
"""

import base64
import os
import uuid
from datetime import datetime
from functools import lru_cache

import httpx
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import InjectedToolArg, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from markdownify import markdownify
from pydantic import BaseModel, Field
from tavily import TavilyClient
from typing_extensions import Annotated, Literal

from app.prompts.prompts import SUMMARIZE_WEB_SEARCH
from app.models.state import DeepAgentState


@lru_cache
def get_summarization_model():
    """Returns a cached instance of the summarization model."""
    return init_chat_model(model="openai:gpt-4o-mini")


@lru_cache
def get_tavily_client():
    """Returns a cached instance of the Tavily client."""
    return TavilyClient()


class Summary(BaseModel):
    """Schema for webpage content summarization."""

    filename: str = Field(description="Name of the file to store.")
    summary: str = Field(description="Key learnings from the webpage.")


class TavilySearchArgs(BaseModel):
    """Pydantic model for Tavily search arguments."""

    query: str = Field(description="Search query to execute")


def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")


def run_tavily_search(
    search_query: str,
    max_results: int = 1,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = True,
) -> dict:
    """Perform search using Tavily API for a single query."""
    tavily_client = get_tavily_client()
    result = tavily_client.search(
        search_query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
    return result


def summarize_webpage_content(webpage_content: str) -> Summary:
    """Summarize webpage content using the configured summarization model."""
    try:
        summarization_model = get_summarization_model()
        structured_model = summarization_model.with_structured_output(Summary)
        summary_and_filename = structured_model.invoke(
            [
                HumanMessage(
                    content=SUMMARIZE_WEB_SEARCH.format(
                        webpage_content=webpage_content, date=get_today_str()
                    )
                )
            ]
        )
        return summary_and_filename
    except Exception:
        return Summary(
            filename="search_result.md",
            summary=(
                webpage_content[:1000] + "..."
                if len(webpage_content) > 1000
                else webpage_content
            ),
        )


def process_search_results(results: dict) -> list[dict]:
    """Process search results by summarizing content where available."""
    processed_results = []
    HTTPX_CLIENT = httpx.Client()
    for result in results.get("results", []):
        url = result["url"]
        try:
            response = HTTPX_CLIENT.get(url, timeout=4.0)
            response.raise_for_status()
            raw_content = markdownify(response.text)
            summary_obj = summarize_webpage_content(raw_content)
        except (httpx.RequestError, httpx.HTTPStatusError):
            raw_content = result.get("raw_content", "")
            summary_obj = Summary(
                filename="URL_error.md",
                summary=result.get("content", "Error reading URL; try another search."),
            )

        uid = (
            base64.urlsafe_b64encode(uuid.uuid4().bytes)
            .rstrip(b"=")
            .decode("ascii")[:8]
        )
        name, ext = os.path.splitext(summary_obj.filename)
        summary_obj.filename = f"{name}_{uid}{ext}"
        processed_results.append(
            {
                "url": result["url"],
                "title": result["title"],
                "summary": summary_obj.summary,
                "filename": summary_obj.filename,
                "raw_content": raw_content,
            }
        )
    return processed_results


# Explicitly define the tool's schema instead of parsing the docstring
@tool(
    args_schema=TavilySearchArgs,
    description=(
        "Search web and save detailed results to files while returning minimal context. "
        "Performs web search and saves full content to files for context offloading. "
        "Returns only essential information to help the agent decide on next steps."
    ),
)
def tavily_search(
    query: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> Command:
    search_results = run_tavily_search(
        query, max_results=max_results, topic=topic, include_raw_content=True
    )
    processed_results = process_search_results(search_results)
    files = state.get("files", {})
    saved_files = []
    summaries = []
    for result in processed_results:
        filename = result["filename"]
        file_content = f"# Search Result: {result['title']}\n\n**URL:** {result['url']}\n**Query:** {query}\n**Date:** {get_today_str()}\n\n## Summary\n{result['summary']}\n\n## Raw Content\n{result['raw_content'] or 'No raw content available'}"
        files[filename] = file_content
        saved_files.append(filename)
        summaries.append(f"- {filename}: {result['summary']}...")
    summary_text = f"🔍 Found {len(processed_results)} result(s) for '{query}':\n\n{chr(10).join(summaries)}\n\nFiles: {', '.join(saved_files)}\n💡 Use read_file() to access full details when needed."
    return Command(
        update={
            "files": files,
            "messages": [ToolMessage(summary_text, tool_call_id=tool_call_id)],
        }
    )


@tool
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making."""
    return f"Reflection recorded: {reflection}"
