import pytest
from app.core.config import get_settings
from app.core.security_headers import build_security_headers
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_security_headers_on_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == "interest-cohort=()"
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]


def test_hsts_only_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("HSTS_ENABLED", "true")
    get_settings.cache_clear()
    headers = build_security_headers(get_settings())
    assert "Strict-Transport-Security" not in headers

    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    headers = build_security_headers(get_settings())
    assert "Strict-Transport-Security" in headers
    assert "max-age=" in headers["Strict-Transport-Security"]
