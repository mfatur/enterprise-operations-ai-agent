"""Deterministic orchestration tests for the sales agent graph."""

import importlib
from unittest.mock import patch

import dotenv
import pytest
import langchain_google_genai
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from backend.tests.conftest import FakeConnection, FakeCursor


class _ImportSafeBoundModel:
    """Default bound model used only while importing the agent module in tests."""

    def invoke(self, messages):
        raise AssertionError("The default Gemini-bound model must not be invoked in tests")


class _ImportSafeGeminiModel:
    """Prevents Gemini client creation while retaining the runtime import shape."""

    def __init__(self, *args, **kwargs):
        self.constructor_args = args
        self.constructor_kwargs = kwargs
        self.bound_model = _ImportSafeBoundModel()

    def bind_tools(self, tools):
        self.tools = tools
        return self.bound_model


_original_load_dotenv = dotenv.load_dotenv
_original_chat_model = langchain_google_genai.ChatGoogleGenerativeAI
dotenv.load_dotenv = lambda *args, **kwargs: False
langchain_google_genai.ChatGoogleGenerativeAI = _ImportSafeGeminiModel
try:
    sales_agent_module = importlib.import_module("backend.app.agents.sales_agent")
finally:
    dotenv.load_dotenv = _original_load_dotenv
    langchain_google_genai.ChatGoogleGenerativeAI = _original_chat_model

from backend.app.tools import sales_tools


class FakeBoundModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.invocations = []

    def invoke(self, messages):
        self.invocations.append(messages)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeModel:
    def __init__(self, bound_model):
        self.bound_model = bound_model
        self.bound_tools = None

    def bind_tools(self, tools):
        self.bound_tools = tools
        return self.bound_model


EXPECTED_TOOL_NAMES = {
    "get_total_revenue",
    "get_revenue_by_region",
    "get_total_quantity_sold",
    "get_top_products",
    "get_top_products_by_revenue",
    "get_average_order_value",
    "get_revenue_by_category",
}


def _bound_tool_name(tool) -> str | None:
    """Return the name from either a plain function or a structured tool."""

    return getattr(tool, "name", None) or getattr(tool, "__name__", None)


def test_agent_node_supplies_system_instruction_and_input_messages():
    response = AIMessage(content="Jawaban singkat")

    with patch.object(
        sales_agent_module.llm_with_tools,
        "invoke",
        return_value=response,
    ) as invoke:
        result = sales_agent_module.agent_node(
            {"messages": [HumanMessage(content="Halo")]}
        )

    messages = invoke.call_args.args[0]
    assert messages[0]["role"] == "system"
    assert "Sales AI Agent" in messages[0]["content"]
    assert "get_top_products ONLY for rankings by quantity" in messages[0]["content"]
    assert "get_top_products_by_revenue for rankings by revenue" in messages[0]["content"]
    assert "Answer in Indonesian" in messages[0]["content"]
    assert messages[1].content == "Halo"
    assert result == {"messages": [response]}


def test_injected_model_binds_all_six_tools_and_returns_final_response():
    bound_model = FakeBoundModel([AIMessage(content="Revenue adalah 100.0")])
    fake_model = FakeModel(bound_model)
    graph = sales_agent_module.create_sales_agent(fake_model)

    result = graph.invoke(
        {"messages": [HumanMessage(content="Berapa total revenue?")]}
    )

    assert {
        _bound_tool_name(tool)
        for tool in fake_model.bound_tools
    } == EXPECTED_TOOL_NAMES
    assert result["messages"][-1].content == "Revenue adalah 100.0"
    assert len(bound_model.invocations) == 1


def test_injected_graph_routes_revenue_tool_result_back_to_model():
    bound_model = FakeBoundModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_total_revenue",
                        "args": {},
                        "id": "revenue-tool-id",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Total revenue adalah 500.0."),
        ]
    )
    graph = sales_agent_module.create_sales_agent(FakeModel(bound_model))
    cursor = FakeCursor(fetchone_result=(500,))

    with patch.object(
        sales_tools,
        "get_connection",
        return_value=FakeConnection(cursor),
    ):
        result = graph.invoke(
            {"messages": [HumanMessage(content="Berapa total revenue?")]}
        )

    assert result["messages"][-1].content == "Total revenue adalah 500.0."
    assert len(bound_model.invocations) == 2
    tool_messages = [
        message
        for message in bound_model.invocations[1]
        if isinstance(message, ToolMessage)
    ]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "get_total_revenue"
    assert tool_messages[0].tool_call_id == "revenue-tool-id"
    assert tool_messages[0].content == "500.0"


def test_injected_graph_preserves_multiple_tool_call_names_ids_and_arguments():
    tool_calls = [
        {
            "name": "get_total_revenue",
            "args": {},
            "id": "multiple-revenue-id",
            "type": "tool_call",
        },
        {
            "name": "get_top_products",
            "args": {"limit": 2},
            "id": "multiple-products-id",
            "type": "tool_call",
        },
    ]
    bound_model = FakeBoundModel(
        [
            AIMessage(content="", tool_calls=tool_calls),
            AIMessage(content="Berikut ringkasan sales."),
        ]
    )
    graph = sales_agent_module.create_sales_agent(FakeModel(bound_model))
    cursor = FakeCursor(fetchone_result=(900,), fetchall_result=[("Laptop", 4)])

    with patch(
        "backend.app.tools.sales_tools.get_connection",
        return_value=FakeConnection(cursor),
    ):
        result = graph.invoke(
            {"messages": [HumanMessage(content="Revenue dan dua produk teratas?")]}
        )

    assert result["messages"][-1].content == "Berikut ringkasan sales."
    second_model_input = bound_model.invocations[1]
    requested_tools = next(
        message for message in second_model_input if isinstance(message, AIMessage)
    )
    assert requested_tools.tool_calls == tool_calls
    returned_tools = [
        message for message in second_model_input if isinstance(message, ToolMessage)
    ]
    assert [(message.name, message.tool_call_id) for message in returned_tools] == [
        ("get_total_revenue", "multiple-revenue-id"),
        ("get_top_products", "multiple-products-id"),
    ]
    assert any(params == (2,) for _, params in cursor.executed)


def test_injected_model_exception_propagates_from_graph():
    bound_model = FakeBoundModel([RuntimeError("fake model failure")])
    graph = sales_agent_module.create_sales_agent(FakeModel(bound_model))

    with pytest.raises(RuntimeError, match="fake model failure"):
        graph.invoke({"messages": [HumanMessage(content="Halo")]})


def test_injected_graph_never_invokes_the_default_gemini_bound_model():
    bound_model = FakeBoundModel([AIMessage(content="Jawaban dari fake model")])
    graph = sales_agent_module.create_sales_agent(FakeModel(bound_model))

    with patch.object(
        sales_agent_module.llm_with_tools,
        "invoke",
        side_effect=AssertionError("Default Gemini path was invoked"),
    ) as default_model_invoke:
        result = graph.invoke({"messages": [HumanMessage(content="Halo")]})

    assert result["messages"][-1].content == "Jawaban dari fake model"
    default_model_invoke.assert_not_called()
