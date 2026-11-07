"""Tests for the local web adapter and its per-session privacy setting."""

import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from src.core.config import settings
from src.web_service import GUIDED_QUESTIONS, execute_question


def test_guided_sales_runs_without_llm(monkeypatch):
    monkeypatch.setattr("src.web_service.llm_enabled", lambda: False)
    response = execute_question(GUIDED_QUESTIONS[0], "guided", False)
    assert response["label"] == "Defined metric"
    assert response["data"].num_rows > 0
    assert "orders" in response["sources"]
    assert response["sql"]


def test_product_breakdown_obeys_protection_and_restores_setting(monkeypatch):
    monkeypatch.setattr(settings, "customer_identifier_protection", False)
    blocked = execute_question(GUIDED_QUESTIONS[-1], "guided", True)
    assert "SENSITIVE_COLUMN_ACCESS" in blocked["error"]
    assert settings.customer_identifier_protection is False
    allowed = execute_question(GUIDED_QUESTIONS[-1], "guided", False)
    assert allowed["data"].num_rows == 10
    assert "repeat_orders" in allowed["data"].column_names


def test_unknown_guided_question_is_not_guessed():
    assert "Choose one" in execute_question("Invent a number", "guided", False)["error"]


def test_setting_restored_when_query_raises(monkeypatch):
    monkeypatch.setattr(settings, "customer_identifier_protection", False)
    monkeypatch.setattr("src.web_service._guided", lambda _: (_ for _ in ()).throw(RuntimeError("failure")))
    with pytest.raises(RuntimeError):
        execute_question("question", "guided", True)
    assert settings.customer_identifier_protection is False


def test_ai_mode_requires_key(monkeypatch):
    monkeypatch.setattr("src.web_service.llm_enabled", lambda: False)
    assert "Sarvam key" in execute_question("question", "ai", False)["error"]


def test_automatic_mode_uses_example_without_key_and_routes_other_questions(monkeypatch):
    monkeypatch.setattr("src.web_service.llm_enabled", lambda: False)
    assert execute_question(GUIDED_QUESTIONS[0], "auto", False)["label"] == "Defined metric"
    assert "Sarvam key" in execute_question("different question", "auto", False)["error"]


def test_category_cohort_analysis():
    q = "Share the Top 10 product categories and the customer new vs repeat share in terms of revenue and also need category % as total of the revenue"
    response = execute_question(q, "auto", False)
    assert response.get("error") is None
    assert response["label"] == "Defined category analysis"
    assert response["data"].num_rows == 10
    assert "category_pct_of_total_revenue" in response["data"].column_names


def test_parallel_sessions_do_not_share_privacy_choice(monkeypatch):
    entered, release = Event(), Event()
    seen = []

    def fake_guided(question):
        seen.append((question, settings.customer_identifier_protection))
        if question == "first":
            entered.set()
            assert release.wait(5)
        return {"ok": True}

    monkeypatch.setattr(settings, "customer_identifier_protection", False)
    monkeypatch.setattr("src.web_service._guided", fake_guided)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(execute_question, "first", "guided", True)
        assert entered.wait(5)
        second = pool.submit(execute_question, "second", "guided", False)
        release.set()
        assert first.result(timeout=5) == {"ok": True}
        assert second.result(timeout=5) == {"ok": True}
    assert seen == [("first", True), ("second", False)]
    assert settings.customer_identifier_protection is False
