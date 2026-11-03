
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


def test_inventory_pagination_and_filtering(monkeypatch):
    monkeypatch.setattr(
        settings, "API_KEY_SECRET", "correct-test-key"
    )

    client = TestClient(app)
    headers = {"X-Api-Key": "correct-test-key"}

    response = client.get(
        "/api/v1/inventory?limit=10&offset=0",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert "limit" in data
    assert "offset" in data
    assert "count" in data
    assert "items" in data

    assert data["limit"] == 10
    assert data["offset"] == 0


def test_inventory_min_stock_filter(monkeypatch):
    monkeypatch.setattr(
        settings, "API_KEY_SECRET", "correct-test-key"
    )

    client = TestClient(app)
    headers = {"X-Api-Key": "correct-test-key"}

    response = client.get(
        "/api/v1/inventory?min_stock=5",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    for item in data["items"]:
        assert item["stock_quantity"] >= 5
        assert item["is_active"] is True
