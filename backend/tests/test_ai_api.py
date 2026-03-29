import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import ai
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("KANBAN_DB_PATH", str(tmp_path / "kanban.db"))

    with TestClient(app) as test_client:
        yield test_client


def sign_in(client: TestClient) -> None:
    response = client.post("/api/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200


def test_ai_test_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/ai/test", json={"prompt": "2+2"})
    assert response.status_code == 401


def test_ai_test_returns_clean_json_when_key_is_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    sign_in(client)
    response = client.post("/api/ai/test", json={"prompt": "What is 2 + 2?"})
    assert response.status_code == 500
    assert response.json() == {"detail": "OPENROUTER_API_KEY environment variable is required"}


def test_ai_test_endpoint_success_with_openrouter(client: TestClient) -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY is required for the live OpenRouter test")

    sign_in(client)

    response = client.post("/api/ai/test", json={"prompt": "Reply with only the number that equals 2 + 2."})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["prompt"] == "Reply with only the number that equals 2 + 2."
    assert "4" in body["answer"]


def test_run_openrouter_prompt_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ai.OpenRouterError, match="OPENROUTER_API_KEY"):
        ai.run_openrouter_prompt("hello")


def test_run_openrouter_prompt_with_mocked_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "4",
                        }
                    }
                ]
            }

    def fake_post(url: str, json: dict[str, object], headers: dict[str, str], timeout: float) -> FakeResponse:
        assert url == ai.OPENROUTER_URL
        assert json["model"] == ai.OPENROUTER_MODEL
        assert json["messages"] == [{"role": "user", "content": "What is 2 + 2?"}]
        assert headers["Authorization"] == "Bearer test-key"
        assert timeout == ai.OPENROUTER_TIMEOUT_SECONDS
        return FakeResponse()

    monkeypatch.setattr(ai.httpx, "post", fake_post)

    result = ai.run_openrouter_prompt("What is 2 + 2?")
    assert result["response_text"] == "4"


def test_ai_chat_applies_operations_and_persists_board(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sign_in(client)

    def fake_prompt(_: str, max_tokens: int = 32) -> dict[str, str]:
        assert max_tokens == 800
        return {
            "prompt": "ignored",
            "response_text": """
            {
              "assistant_message": "I renamed the column and added the card.",
              "operations": [
                {"type": "rename_column", "column_id": "todo", "title": "Next Up"},
                {
                  "type": "create_card",
                  "column_id": "todo",
                  "card_id": "card-7",
                  "title": "Plan release notes",
                  "details": "Draft the MVP release summary."
                }
              ]
            }
            """,
        }

    monkeypatch.setattr("app.main.run_openrouter_prompt", fake_prompt)

    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Rename To Do to Next Up and add a release notes card there.",
            "history": [{"role": "user", "content": "Let's clean up the board."}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"] == "I renamed the column and added the card."
    assert body["operations"][0]["type"] == "rename_column"
    assert body["board"]["columns"][1]["title"] == "Next Up"
    assert body["board"]["columns"][1]["cards"][-1]["id"] == "card-7"

    board_response = client.get("/api/board")
    assert board_response.status_code == 200
    saved_board = board_response.json()
    assert saved_board["columns"][1]["title"] == "Next Up"
    assert saved_board["columns"][1]["cards"][-1]["id"] == "card-7"
