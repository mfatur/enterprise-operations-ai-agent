import logging
import os
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from backend.app.database.connection import get_connection


logger = logging.getLogger(__name__)

from backend.app.tools.sales_tools import (
    get_total_revenue,
    get_revenue_by_region,
    get_total_quantity_sold,
    get_top_products,
    get_top_products_by_revenue,
    get_average_order_value,
    get_revenue_by_category,
)


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable is not set. Set GEMINI_API_KEY to use the Gemini model.")
    raise ValueError("GEMINI_API_KEY environment variable is required")


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0,
)


tools = [
    get_total_revenue,
    get_revenue_by_region,
    get_total_quantity_sold,
    get_top_products,
    get_top_products_by_revenue,
    get_average_order_value,
    get_revenue_by_category,
]

llm_with_tools = llm.bind_tools(tools)


def agent_node(
    state: AgentState,
    model_with_tools=None,
):
    logger.info("Sales agent started")

    system_message = """
You are a Sales AI Agent for an enterprise operations system.

Your job is to answer questions about sales data stored in the database.

Rules:
1. For questions requiring sales data, ALWAYS use the available tools.
2. Never invent or guess numerical results.
3. Use the most appropriate tool for the user's question.
4. Use get_top_products ONLY for rankings by quantity, units sold, or number of items sold.
5. Use get_top_products_by_revenue for rankings by revenue, sales value, turnover, monetary value, or similar financial value.
6. If a question requires multiple pieces of sales information, you may use multiple tools.
7. After receiving tool results, explain the answer clearly and concisely.
8. Answer in Indonesian.
"""

    messages = [
        {
            "role": "system",
            "content": system_message,
        },
        *state["messages"],
    ]

    active_model = model_with_tools or llm_with_tools
    response = active_model.invoke(messages)

    logger.info("Sales agent response generated")

    if getattr(response, "tool_calls", None):
        tool_names = [
            tool_call["name"]
            for tool_call in response.tool_calls
        ]

        logger.info(
            "Tools requested by agent: %s",
            tool_names
        )

    return {
        "messages": [response]
    }


def create_sales_agent(model):
    """Compile a sales-agent graph using an explicitly supplied chat model.

    The runtime graph below continues to use the configured Gemini model. This
    factory provides an isolated construction seam for callers that need a
    different model implementation, such as deterministic unit tests.
    """

    model_with_tools = model.bind_tools(tools)
    injected_tool_node = ToolNode(tools)
    injected_graph_builder = StateGraph(AgentState)
    injected_graph_builder.add_node(
        "agent",
        lambda state: agent_node(state, model_with_tools),
    )
    injected_graph_builder.add_node("tools", injected_tool_node)
    injected_graph_builder.add_edge(START, "agent")
    injected_graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
    )
    injected_graph_builder.add_edge("tools", "agent")

    return injected_graph_builder.compile()


tool_node = ToolNode(tools)


graph_builder = StateGraph(AgentState)


graph_builder.add_node(
    "agent",
    agent_node,
)

graph_builder.add_node(
    "tools",
    tool_node,
)


graph_builder.add_edge(
    START,
    "agent",
)


graph_builder.add_conditional_edges(
    "agent",
    tools_condition,
)


graph_builder.add_edge(
    "tools",
    "agent",
)


sales_agent = graph_builder.compile()
