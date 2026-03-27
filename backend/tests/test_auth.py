from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import SESSION_COOKIE, app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("KANBAN_DB_PATH", str(tmp_path / "kanban.db"))

    with TestClient(app) as test_client:
        yield test_client


def test_session_defaults_to_guest(client: TestClient) -> None:
    response = client.get("/api/session")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_login_accepts_dummy_credentials_and_sets_cookie(client: TestClient) -> None:
    response = client.post("/api/login", json={"username": "user", "password": "password"})

    assert response.status_code == 200
    assert response.json() == {"authenticated": True, "username": "user"}
    assert response.cookies.get(SESSION_COOKIE) == "user"


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post("/api/login", json={"username": "wrong", "password": "password"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_logout_clears_session_cookie(client: TestClient) -> None:
    login_response = client.post("/api/login", json={"username": "user", "password": "password"})

    assert login_response.status_code == 200

    session_response = client.get("/api/session")
    assert session_response.json() == {"authenticated": True, "username": "user"}

    logout_response = client.post("/api/logout")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False}

    final_session_response = client.get("/api/session")
    assert final_session_response.json() == {"authenticated": False}
