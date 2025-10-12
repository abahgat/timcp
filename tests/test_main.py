from fastapi.testclient import TestClient
import pytest
import os


@pytest.fixture(scope="module")
def client():
    # Set the required environment variable before the app is imported
    os.environ["TRAVEL_IMPACT_MODEL_API_KEY"] = "test-key"

    # Import app after setting env var
    from mcp_tim_wrapper.main import app

    # Use TestClient with raise_server_exceptions=False to allow testing
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_health_check(client):
    """
    Tests the /health endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_headers_on_mcp_endpoint(client):
    """
    Tests that CORS headers are properly set on the /mcp endpoint.
    """
    # Test OPTIONS preflight request
    response = client.options(
        "/mcp",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-credentials" in response.headers
    # Verify allowed methods include POST for MCP
    assert "POST" in response.headers["access-control-allow-methods"]


def test_cors_allows_localhost_origins(client):
    """
    Tests that localhost origins are allowed by CORS configuration.
    """
    response = client.options(
        "/mcp",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers


def test_cors_max_age_configured(client):
    """
    Tests that CORS max-age is properly configured for performance.
    """
    response = client.options(
        "/mcp",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert "access-control-max-age" in response.headers
    # Verify max-age is set to 24 hours (86400 seconds)
    assert response.headers["access-control-max-age"] == "86400"
