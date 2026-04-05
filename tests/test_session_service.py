from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.db import session_service


def _make_response(error=None, data=None):
    return SimpleNamespace(error=error, data=data)


def test_require_success_returns_data():
    resp = _make_response(error=None, data={"ok": True})
    assert session_service._require_success(resp, "Op") == {"ok": True}


def test_require_success_raises_runtimeerror_on_error():
    resp = _make_response(error="bad", data=None)
    with pytest.raises(RuntimeError) as exc:
        session_service._require_success(resp, "Save")
    assert "Save failed: bad" in str(exc.value)


def test_save_study_session_inserts_expected_payload_and_returns_data():
    mock_table = MagicMock()
    mock_table.insert.return_value = mock_table
    mock_table.execute.return_value = _make_response(error=None, data=[{"id": "abc"}])

    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    with patch.object(session_service.supabase, "_instance", mock_client):
        result = session_service.save_study_session(
            "input text",
            "a summary",
            [{"q": 1}],
            [{"f": 1}],
            filename="file.pdf",
        )

    expected = {
        "input_text": "input text",
        "summary": "a summary",
        "quiz_json": [{"q": 1}],
        "flashcards_json": [{"f": 1}],
        "filename": "file.pdf",
    }

    mock_table.insert.assert_called_once_with(expected)
    assert result == [{"id": "abc"}]


def test_get_all_study_sessions_formats_and_returns_list():
    long_text = "x" * 100
    sample_data = [
        {"id": "1", "input_text": "Short text", "created_at": "2026-04-04T10:00:00Z"},
        {"id": "2", "input_text": long_text, "created_at": "2026-04-04T09:00:00Z"},
        {"id": "3", "created_at": "2026-04-04T08:00:00Z"},
    ]

    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.execute.return_value = _make_response(error=None, data=sample_data)

    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    with patch.object(session_service.supabase, "_instance", mock_client):
        result = session_service.get_all_study_sessions()

    by_id = {r["id"]: r for r in result}
    assert by_id["1"]["filename"] == "Short text"
    assert by_id["2"]["filename"] == ("x" * 50) + "..."
    assert by_id["3"]["filename"] == "Session #3"


def test_get_study_session_by_id_returns_item_or_none():
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = _make_response(
        error=None,
        data=[{"id": "42", "input_text": "abc"}],
    )

    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    with patch.object(session_service.supabase, "_instance", mock_client):
        item = session_service.get_study_session_by_id("42")

    assert item["id"] == "42"

    mock_table.execute.return_value = _make_response(error=None, data=[])

    with patch.object(session_service.supabase, "_instance", mock_client):
        none_item = session_service.get_study_session_by_id("missing")

    assert none_item is None