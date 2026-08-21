"""Deterministic component tests for the sales LangGraph ToolNode."""

import json
from unittest.mock import patch

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from backend.app.tools import sales_tools
from backend.tests.conftest import FakeConnection, FakeCursor


SALES_TOOLS = [
    sales_tools.get_total_revenue,
    sales_tools.get_revenue_by_region,
    sales_tools.get_total_quantity_sold,
    sales_tools.get_top_products,
    sales_tools.get_top_products_by_revenue,
    sales_tools.get_average_order_value,
    sales_tools.get_revenue_by_category,
]

EXPECTED_TOOL_NAMES = {
    "get_total_revenue",
    "get_revenue_by_region",
    "get_total_quantity_sold",
    "get_top_products",
    "get_top_products_by_revenue",
    "get_average_order_value",
    "get_revenue_by_category",
}


def _tool_node() -> ToolNode:
    return ToolNode(SALES_TOOLS)


def _invoke_tool_calls(tool_node: ToolNode, tool_calls: list[dict]) -> list[ToolMessage]:
    result = tool_node.invoke(
        {"messages": [AIMessage(content="", tool_calls=tool_calls)]}
    )
    return result["messages"]


def test_sales_tool_node_registers_all_six_sales_tools():
    tool_node = _tool_node()

    assert set(tool_node.tools_by_name) == EXPECTED_TOOL_NAMES


def test_tool_node_executes_total_revenue_and_returns_tool_message():
    cursor = FakeCursor(fetchone_result=(1250.5,))
    tool_node = _tool_node()
    tool_call = {
        "name": "get_total_revenue",
        "args": {},
        "id": "revenue-call-1",
        "type": "tool_call",
    }

    with patch.object(
        sales_tools,
        "get_connection",
        return_value=FakeConnection(cursor),
    ):
        messages = _invoke_tool_calls(tool_node, [tool_call])

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, ToolMessage)
    assert message.name == "get_total_revenue"
    assert message.tool_call_id == "revenue-call-1"
    assert message.status == "success"
    assert message.content == "1250.5"


def test_tool_node_forwards_top_products_limit_and_serializes_result():
    cursor = FakeCursor(fetchall_result=[("Laptop", 9), ("Monitor", 4)])
    tool_node = _tool_node()
    tool_call = {
        "name": "get_top_products",
        "args": {"limit": 2},
        "id": "top-products-call-2",
        "type": "tool_call",
    }

    with patch.object(
        sales_tools,
        "get_connection",
        return_value=FakeConnection(cursor),
    ):
        messages = _invoke_tool_calls(tool_node, [tool_call])

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, ToolMessage)
    assert message.tool_call_id == "top-products-call-2"
    assert message.status == "success"
    assert json.loads(message.content) == [
        {"product": "Laptop", "total_quantity": 9},
        {"product": "Monitor", "total_quantity": 4},
    ]
    assert cursor.executed[0][1] == (2,)


def test_tool_node_preserves_ids_for_multiple_tool_calls():
    cursor = FakeCursor(fetchone_result=(8,))
    tool_node = _tool_node()
    tool_calls = [
        {
            "name": "get_total_revenue",
            "args": {},
            "id": "multiple-revenue-id",
            "type": "tool_call",
        },
        {
            "name": "get_total_quantity_sold",
            "args": {},
            "id": "multiple-quantity-id",
            "type": "tool_call",
        },
    ]

    with patch.object(
        sales_tools,
        "get_connection",
        return_value=FakeConnection(cursor),
    ):
        messages = _invoke_tool_calls(tool_node, tool_calls)

    assert all(isinstance(message, ToolMessage) for message in messages)
    assert [message.tool_call_id for message in messages] == [
        "multiple-revenue-id",
        "multiple-quantity-id",
    ]
    assert [message.content for message in messages] == ["8.0", "8"]
    assert [message.status for message in messages] == ["success", "success"]


def test_tool_node_returns_error_tool_message_for_unknown_tool():
    tool_node = _tool_node()
    tool_call = {
        "name": "missing_sales_tool",
        "args": {},
        "id": "unknown-tool-id",
        "type": "tool_call",
    }

    messages = _invoke_tool_calls(tool_node, [tool_call])

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, ToolMessage)
    assert message.name == "missing_sales_tool"
    assert message.tool_call_id == "unknown-tool-id"
    assert message.status == "error"
    assert message.content == (
        "Error: missing_sales_tool is not a valid tool, try one of "
        "[get_total_revenue, get_revenue_by_region, get_total_quantity_sold, "
        "get_top_products, get_top_products_by_revenue, get_average_order_value, "
        "get_revenue_by_category]."
    )
