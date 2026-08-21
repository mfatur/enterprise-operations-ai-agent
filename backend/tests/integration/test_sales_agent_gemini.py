"""Opt-in smoke test for the real Gemini-backed sales-agent graph."""

import importlib

import pytest
from langchain_core.messages import AIMessage, HumanMessage


pytestmark = [
    pytest.mark.integration,
    pytest.mark.gemini,
    pytest.mark.smoke,
]


def _final_response_text(content) -> str:
    """Extract text without assuming one Gemini content representation."""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()

    return ""


def test_sales_agent_gemini_smoke():
    """Run one intentional, non-deterministic end-to-end agent invocation."""

    # This import is deliberately inside the opt-in test. It uses the
    # application's existing configuration mechanism only after a developer
    # intentionally selects the Gemini marker.
    agent_module = importlib.import_module("backend.app.agents.sales_agent")

    if not agent_module.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY is required for Gemini integration tests")

    try:
        result = agent_module.sales_agent.invoke(
            {
                "messages": [
                    HumanMessage(content="Berapa total revenue?")
                ]
            }
        )
    except Exception as error:
        pytest.fail(
            "Gemini smoke test could not complete "
            f"({type(error).__name__}); verify the intentionally selected "
            "provider and database integration environment."
        )

    messages = result.get("messages", [])
    assert messages, "The sales-agent graph returned no messages"

    final_message = messages[-1]
    assert isinstance(final_message, AIMessage)

    final_text = _final_response_text(final_message.content)
    assert final_text, "The final Gemini response contained no text"
    assert not final_text.startswith("Error:"), (
        "The final Gemini response was a raw tool error rather than useful text"
    )
