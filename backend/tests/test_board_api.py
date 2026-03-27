from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("KANBAN_DB_PATH", str(tmp_path / "kanban.db"))

    with TestClient(app) as test_client:
        yield test_client


def sign_in(client: TestClient) -> None:
    response = client.post("/api/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200


def test_board_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/board")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_authenticated_user_receives_seeded_board(client: TestClient) -> None:
    sign_in(client)

    response = client.get("/api/board")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["columns"]) == 5
    assert payload["columns"][0]["id"] == "backlog"
    assert payload["columns"][0]["cards"][0]["id"] == "card-1"


def test_put_board_persists_changes(client: TestClient) -> None:
    sign_in(client)

    board = client.get("/api/board").json()
    board["columns"][0]["title"] = "Ideas"
    board["columns"][0]["cards"].append(
        {
            "id": "card-99",
            "title": "Persisted task",
            "details": "Saved through the API.",
        }
    )

    update_response = client.put("/api/board", json=board)

    assert update_response.status_code == 200
    assert update_response.json()["columns"][0]["title"] == "Ideas"

    read_response = client.get("/api/board")

    assert read_response.status_code == 200
    persisted = read_response.json()
    assert persisted["columns"][0]["title"] == "Ideas"
    assert persisted["columns"][0]["cards"][-1]["id"] == "card-99"
