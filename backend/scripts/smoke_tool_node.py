from langchain_core.messages import ToolCall, AIMessage
from langgraph.prebuilt import ToolNode

from backend.app.tools.sales_tools import (
    get_total_revenue,
    get_revenue_by_region,
    get_total_quantity_sold,
    get_top_products,
    get_average_order_value,
    get_revenue_by_category,
)


tools = [
    get_total_revenue,
    get_revenue_by_region,
    get_total_quantity_sold,
    get_top_products,
    get_average_order_value,
    get_revenue_by_category,
]

tool_node = ToolNode(tools)


print("=== TOOL NODE TEST ===")

tool_calls = [
    {
        "name": "get_total_revenue",
        "args": {},
        "id": "test_revenue",
        "type": "tool_call",
    }
]

message = AIMessage(
    content="",
    tool_calls=tool_calls,
)

result = tool_node.invoke(
    {
        "messages": [message]
    }
)

print("\nTool: get_total_revenue")
print("Result:", result)

print("\n=== TOOL NODE TEST PASSED ===")