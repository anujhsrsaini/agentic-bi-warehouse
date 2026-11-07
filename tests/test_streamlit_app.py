"""Smoke test the interface without requiring a browser or an API key."""

import pytest
from pathlib import Path

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest
from streamlit_app import split_analysis


def test_analysis_text_is_split_into_scannable_parts():
    text = "**Takeaway**\nTop 10 customers contribute half a percent.\n\n**Key points**\n- Largest is R$13,440.\n- Next is R$7,388.\n\n**Caveats**\n- Delivered orders only."
    takeaway, points, caveats, remainder = split_analysis(text)
    assert takeaway == "Top 10 customers contribute half a percent."
    assert points == ["Largest is R$13,440.", "Next is R$7,388."]
    assert caveats == ["Delivered orders only."]
    assert remainder == text


def test_guided_question_button_displays_result():
    app = AppTest.from_file(Path(__file__).resolve().parent.parent / "streamlit_app.py", default_timeout=30).run()
    assert not app.exception
    next(button for button in app.button if "Sales by state" in button.label).click().run()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert not app.radio
    assert any("Defined metric" in item.value for item in app.caption)
    assert any("What I found" in item.value for item in app.markdown)


def test_product_breakdown_has_readable_sections():
    app = AppTest.from_file(Path(__file__).resolve().parent.parent / "streamlit_app.py", default_timeout=30).run()
    next(button for button in app.button if "New vs. repeat" in button.label).click().run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Overview", "Orders & customers", "Units & revenue"]
    assert len(app.dataframe) == 3
