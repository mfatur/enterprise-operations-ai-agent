"""Deterministic FastAPI endpoint tests with the sales agent isolated."""

import importlib
from types import SimpleNamespace
from unittest.mock import patch

import dotenv
import langchain_google_genai
import pytest
from fastapi.testclient import TestClient


class _ImportSafeGeminiModel:
    """Stops agent-module import from constructing a real Gemini client."""

    def __init__(self, *args, **kwargs):
        pass

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        raise AssertionError("The default Gemini model must not be invoked in API tests")


_original_load_dotenv = dotenv.load_dotenv
_original_chat_model = langchain_google_genai.ChatGoogleGenerativeAI
dotenv.load_dotenv = lambda *args, **kwargs: False
langchain_google_genai.ChatGoogleGenerativeAI = _ImportSafeGeminiModel
try:
    main_module = importlib.import_module("backend.app.main")
finally:
    dotenv.load_dotenv = _original_load_dotenv
    langchain_google_genai.ChatGoogleGenerativeAI = _original_chat_model


client = TestClient(main_module.app)


def _agent_result(content):
    return {"messages": [SimpleNamespace(content=content)]}


def test_root_returns_expected_health_payload():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Enterprise Operations AI Agent is running"
    }


def test_chat_returns_mocked_answer_for_valid_question():
    with patch.object(
        main_module.sales_agent,
        "invoke",
        return_value=_agent_result("Revenue adalah 100.0"),
    ) as invoke:
        response = client.post("/chat", json={"question": "Berapa total revenue?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "Revenue adalah 100.0"}
    invoke.assert_called_once()


@pytest.mark.parametrize(
    ("question", "status_code"),
    [
        ("", 422),
        ("   ", 400),
        ("hi", 422),
    ],
)
def test_chat_rejects_invalid_questions(question, status_code):
    with patch.object(
        main_module.sales_agent,
        "invoke",
        side_effect=AssertionError("Agent must not run for invalid input"),
    ) as invoke:
        response = client.post("/chat", json={"question": question})

    assert response.status_code == status_code
    invoke.assert_not_called()


def test_chat_returns_plain_text_final_message_content():
    with patch.object(
        main_module.sales_agent,
        "invoke",
        return_value=_agent_result("Jawaban teks biasa"),
    ) as invoke:
        response = client.post("/chat", json={"question": "Tampilkan ringkasan sales"})

    assert response.status_code == 200
    assert response.json() == {"answer": "Jawaban teks biasa"}
    invoke.assert_called_once()


def test_chat_concatenates_text_blocks_from_final_message_content():
    blocks = [
        {"type": "text", "text": "Revenue: 100. "},
        {"type": "image", "url": "ignored"},
        {"type": "text", "text": "Jumlah produk: 5."},
    ]

    with patch.object(
        main_module.sales_agent,
        "invoke",
        return_value=_agent_result(blocks),
    ) as invoke:
        response = client.post("/chat", json={"question": "Berikan ringkasan sales"})

    assert response.status_code == 200
    assert response.json() == {"answer": "Revenue: 100. Jumlah produk: 5."}
    invoke.assert_called_once()


@pytest.mark.parametrize("error_message", ["429 quota exceeded", "RESOURCE_EXHAUSTED"])
def test_chat_maps_gemini_quota_errors_to_503(error_message):
    with patch.object(
        main_module.sales_agent,
        "invoke",
        side_effect=RuntimeError(error_message),
    ) as invoke:
        response = client.post("/chat", json={"question": "Berapa total revenue?"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Layanan AI sedang mencapai batas penggunaan Gemini API. "
        "Silakan coba lagi nanti."
    }
    invoke.assert_called_once()


@pytest.mark.parametrize("error_message", ["503 service unavailable", "UNAVAILABLE"])
def test_chat_maps_gemini_unavailable_errors_to_503(error_message):
    with patch.object(
        main_module.sales_agent,
        "invoke",
        side_effect=RuntimeError(error_message),
    ) as invoke:
        response = client.post("/chat", json={"question": "Berapa total revenue?"})

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Model AI sedang tidak tersedia. Silakan coba lagi beberapa saat."
    }
    invoke.assert_called_once()


def test_chat_maps_generic_agent_errors_to_500():
    with patch.object(
        main_module.sales_agent,
        "invoke",
        side_effect=RuntimeError("unexpected failure"),
    ) as invoke:
        response = client.post("/chat", json={"question": "Berapa total revenue?"})

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Terjadi kesalahan internal pada AI Agent."
    }
    invoke.assert_called_once()
