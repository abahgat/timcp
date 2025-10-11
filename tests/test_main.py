from fastapi.testclient import TestClient
import pytest
from mcp_tim_wrapper.main import app

@pytest.fixture
def client(monkeypatch):
    # Set the required environment variable before the app and TestClient are created.
    monkeypatch.setenv("TRAVEL_IMPACT_MODEL_API_KEY", "test-key")
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    """
    Tests the /health endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
