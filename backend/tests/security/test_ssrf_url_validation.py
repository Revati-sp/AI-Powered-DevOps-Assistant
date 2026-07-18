import pytest
from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services.llm.url_validation import chat_completions_url, validate_llm_base_url


@pytest.fixture(autouse=True)
def _mock_public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(
        host: str, *args: object, **kwargs: object
    ) -> list[tuple[int, int, int, str, tuple[str, int]]]:
        if host == "internal.example":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))]
        if host in {"api.example.com", "example.com"}:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        return real_getaddrinfo(host, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(
        "app.services.llm.url_validation.socket.getaddrinfo", fake_getaddrinfo
    )
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_rejects_http_without_insecure_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_INSECURE_LLM_HTTP", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError):
        validate_llm_base_url("http://example.com/v1", provider="llama")


def test_rejects_credentials_in_url(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError):
        validate_llm_base_url("https://user:pass@example.com/v1", provider="llama")


def test_rejects_fragment(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="fragment"):
        validate_llm_base_url("https://example.com/v1#secret", provider="llama")


def test_rejects_private_literal_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="private"):
        validate_llm_base_url("https://192.168.1.10/v1", provider="llama")


def test_rejects_loopback_when_private_not_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "false")
    monkeypatch.setenv("ALLOW_INSECURE_LLM_HTTP", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="private"):
        validate_llm_base_url("https://127.0.0.1/v1", provider="llama")


def test_allows_localhost_with_insecure_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_INSECURE_LLM_HTTP", "true")
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "false")
    get_settings.cache_clear()
    url = validate_llm_base_url("http://localhost:11434/v1", provider="llama")
    assert url == "http://localhost:11434/v1"


def test_enforces_host_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_LLM_HOSTS", "api.example.com")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="allowlist"):
        validate_llm_base_url("https://other.example.com/v1", provider="llama")
    url = validate_llm_base_url("https://api.example.com/v1", provider="llama")
    assert url == "https://api.example.com/v1"


def test_rejects_resolved_private_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="private"):
        validate_llm_base_url("https://internal.example/v1", provider="llama")


def test_chat_completions_url_join() -> None:
    assert (
        chat_completions_url("https://example.com/v1/")
        == "https://example.com/v1/chat/completions"
    )
    assert (
        chat_completions_url("https://example.com/v1/chat/completions")
        == "https://example.com/v1/chat/completions"
    )


def test_rejects_empty_url(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="not configured"):
        validate_llm_base_url("   ", provider="mistral")


def test_rejects_unsupported_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="scheme"):
        validate_llm_base_url("ftp://example.com/v1", provider="llama")


def test_rejects_link_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="private"):
        validate_llm_base_url("https://169.254.1.1/v1", provider="llama")


def test_rejects_private_ipv6(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="private"):
        validate_llm_base_url("https://[fd00::1]/v1", provider="llama")


def test_allows_private_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "true")
    get_settings.cache_clear()
    url = validate_llm_base_url("https://10.0.0.8/v1", provider="llama")
    assert url == "https://10.0.0.8/v1"


def test_dns_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def boom(*_a: object, **_k: object) -> list[object]:
        raise socket.gaierror("no such host")

    monkeypatch.setattr("app.services.llm.url_validation.socket.getaddrinfo", boom)
    monkeypatch.setenv("ALLOW_PRIVATE_LLM_NETWORKS", "false")
    get_settings.cache_clear()
    with pytest.raises(ValidationAppError, match="Unable to resolve"):
        validate_llm_base_url("https://missing.invalid/v1", provider="llama")
