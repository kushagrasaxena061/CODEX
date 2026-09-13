import pytest
from fastapi.testclient import TestClient
from backend.main import app

# Create a synchronous test client for our FastAPI app
client = TestClient(app)

def test_cors_headers():
    """Verify that CORS is properly configured for the React frontend."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/api/chat", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

def test_chat_endpoint():
    """Verify the frontend can successfully submit a prompt."""
    response = client.post("/api/chat", json={"prompt": "Build a header component"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["prompt"] == "Build a header component"

def test_status_endpoint():
    """Verify the frontend can poll the agent's status."""
    response = client.get("/api/status")
    
    assert response.status_code == 200
    assert response.json()["status"] == "idle"
