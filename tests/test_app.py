"""Smoke tests for the Streamlit UI (uses Streamlit's built-in AppTest).
They run app.py headless and click the buttons, so crashes show up here
instead of in the demo."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _run_from_project_root(monkeypatch):
    monkeypatch.chdir(ROOT)      # app.py reads data/ with relative paths


def _app():
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()


def _button(at, label):
    for b in list(at.sidebar.button) + list(at.button):
        if b.label == label:
            return b
    raise AssertionError(f"button {label!r} not found")


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def test_sample_city_loads_without_error():
    at = _app()
    assert not at.exception
    assert not at.error


def test_find_route_shows_a_hospital():
    at = _app()
    _button(at, "Find route").click().run()
    assert not at.exception
    assert "Nearest hospital" in _metrics(at)


def test_block_three_random_roads_does_not_crash():
    at = _app()
    _button(at, "Find route").click().run()
    _button(at, "Block 3 random roads").click().run()
    assert not at.exception
    assert len(at.sidebar.multiselect(key="blocked_sel").value) == 3


def test_result_is_hidden_after_settings_change():
    at = _app()
    _button(at, "Find route").click().run()
    assert "Nearest hospital" in _metrics(at)
    at.sidebar.radio[1].set_value("time").run()   # weight mode changed
    assert not at.exception
    assert "Nearest hospital" not in _metrics(at)


def test_no_hospital_selected_shows_clear_message():
    at = _app()
    at.sidebar.multiselect(key="hosp_sel").set_value([]).run()
    _button(at, "Find route").click().run()
    assert not at.exception
    assert any("at least one hospital" in w.value for w in at.warning)


def test_manual_entry_default_city_works():
    at = _app()
    at.sidebar.radio(key="src").set_value("Enter manually").run()
    assert not at.exception and not at.error
    _button(at, "Find route").click().run()
    assert not at.exception
    assert "Nearest hospital" in _metrics(at)


def test_random_city_works():
    at = _app()
    at.sidebar.radio(key="src").set_value("Random city").run()
    assert not at.exception
    _button(at, "Find route").click().run()
    assert not at.exception
    assert "Nearest hospital" in _metrics(at)
