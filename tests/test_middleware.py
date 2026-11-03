
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    return TestClient(app)


def test_missing_api_key_returns_401(client):
    response = client.get("/api/v1/inventory")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key"
    }


def test_invalid_api_key_returns_401(client, monkeypatch):
    monkeypatch.setattr(
        settings, "API_KEY_SECRET", "correct-test-key"
    )

    response = client.get(
        "/api/v1/inventory",
        headers={"X-Api-Key": "wrong-test-key"},
    )

    assert response.status_code == 401


def test_valid_api_key_is_accepted(client, monkeypatch):
    monkeypatch.setattr(
        settings, "API_KEY_SECRET", "correct-test-key"
    )

    response = client.get(
        "/api/v1/inventory",
        headers={"X-Api-Key": "correct-test-key"},
    )

    # The request passes middleware authentication.
    # It may return an empty inventory or another valid
    # endpoint response, depending on the database state.
    assert response.status_code == 200
