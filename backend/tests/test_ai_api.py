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
