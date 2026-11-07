"""Configuration tests use a temporary example key, never real credentials."""

from src.core.config import Settings


def test_customer_identifier_protection_is_off_by_default(monkeypatch):
    monkeypatch.delenv("AGENTIC_BI_CUSTOMER_IDENTIFIER_PROTECTION", raising=False)
    assert Settings(_env_file=None).customer_identifier_protection is False


def test_sarvam_key_is_loaded_from_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    monkeypatch.delenv("AGENTIC_BI_SARVAM_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("SARVAM_API_KEY=test-local-key\n", encoding="utf-8")
    assert Settings(_env_file=env_file).sarvam_api_key == "test-local-key"


def test_prefixed_sarvam_key_is_supported(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    monkeypatch.setenv("AGENTIC_BI_SARVAM_API_KEY", "test-prefixed-key")
    assert Settings(_env_file=None).sarvam_api_key == "test-prefixed-key"
