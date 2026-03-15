import pytest
from app.config import settings

@pytest.mark.asyncio
async def test_api_key_auth_enforced(async_client):
    """Verify that requests without the API Key are rejected."""
    # Attempting to access memory list without key
    response = await async_client.get("/api/v1/memory/")
    assert response.status_code == 401
    assert "Invalid API Key" in response.json()["message"]

@pytest.mark.asyncio
async def test_api_key_auth_success(async_client):
    """Verify that requests with the valid API Key are accepted."""
    headers = {"X-API-Key": settings.API_KEY}
    response = await async_client.get("/api/v1/memory/", headers=headers)
    # The endpoint might return 200 [] or fail if DB isn't initialized, but it shouldn't be 401
    assert response.status_code != 401

@pytest.mark.asyncio
async def test_rate_limiting_enforced(async_client):
    """Verify that hitting an endpoint too quickly triggers the rate limiter."""
    headers = {"X-API-Key": settings.API_KEY}
    
    # settings.RATE_LIMIT_VOICE is 10/minute, let's spam it 11 times.
    for _ in range(10):
        # We send empty requests to trigger Validation or 400 early, 
        # but the limiter fires before endpoint logic anyway.
        res = await async_client.post("/api/v1/voice/synthesize", json={"text": "Hello"}, headers=headers)
        # It shouldn't be 429 yet
        assert res.status_code != 429
        
    # The 11th should be rate-limited
    res_limited = await async_client.post("/api/v1/voice/synthesize", json={"text": "Hello"}, headers=headers)
    assert res_limited.status_code == 429
    assert "error" in res_limited.json()
