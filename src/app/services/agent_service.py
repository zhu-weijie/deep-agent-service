from datetime import datetime

from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

# Imports from our new project structure
from app.tools.file_tools import ls, read_file, write_file
from app.tools.todo_tools import read_todos, write_todos
from app.tools.research_tools import tavily_search, think_tool, get_today_str
from app.tools.task_tool import _create_task_tool
from app.models.state import DeepAgentState
from app.prompts.prompts import (
    RESEARCHER_INSTRUCTIONS,
    SUBAGENT_USAGE_INSTRUCTIONS,
    TODO_USAGE_INSTRUCTIONS,
    FILE_USAGE_INSTRUCTIONS,
)


def create_deep_agent():
    """
    Factory function to create the main Deep Agent graph.
    """
    # Initialize the primary language model
    model = init_chat_model(model="anthropic:claude-sonnet-4-20250514", temperature=0.0)

    # --- Define Tools ---
    # Tools for the research sub-agent
    sub_agent_tools = [tavily_search, think_tool]

    # Tools available to the main agent
    built_in_tools = [ls, read_file, write_file, write_todos, read_todos, think_tool]

    # --- Define Research Sub-Agent ---
    research_sub_agent = {
        "name": "research-agent",
        "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
        "prompt": RESEARCHER_INSTRUCTIONS.format(date=get_today_str()),
        "tools": ["tavily_search", "think_tool"],
    }

    # --- Create the Task Tool for Delegation ---
    task_tool = _create_task_tool(
        sub_agent_tools, [research_sub_agent], model, DeepAgentState
    )

    # Combine all tools available to the main agent
    delegation_tools = [task_tool]
    all_tools = sub_agent_tools + built_in_tools + delegation_tools

    # --- Construct the Main Agent Prompt ---
    # Define hardcoded limits
    max_concurrent_research_units = 3
    max_researcher_iterations = 3

    subagent_instructions = SUBAGENT_USAGE_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
        date=datetime.now().strftime("%a %b %-d, %Y"),
    )

    # Combine all prompt sections
    instructions = (
        "# TODO MANAGEMENT\n"
        + TODO_USAGE_INSTRUCTIONS
        + "\n\n"
        + "=" * 80
        + "\n\n"
        + "# FILE SYSTEM USAGE\n"
        + FILE_USAGE_INSTRUCTIONS
        + "\n\n"
        + "=" * 80
        + "\n\n"
        + "# SUB-AGENT DELEGATION\n"
        + subagent_instructions
    )

    # --- Create the Agent ---
    agent = create_react_agent(
        model, all_tools, prompt=instructions, state_schema=DeepAgentState
    )

    print("Deep Agent graph created successfully.")
    return agent


# Create a single, reusable instance of the agent to be used by the API
agent_executor = create_deep_agent()

# --- Validation Block ---
if __name__ == "__main__":
    # This block will only run when the script is executed directly
    # It allows us to validate that the agent can be created without errors.
    print("Agent service module loaded and agent instance created.")
    # In a real application, you might add more robust tests here.
