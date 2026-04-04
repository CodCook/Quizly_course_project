from unittest.mock import patch


def test_fetch_all_history_returns_sessions(client):
    sample = [
        {
            "id": "1",
            "input_text": "Sample text",
            "created_at": "2026-04-04T10:00:00Z",
        }
    ]

    with patch("app.routes.history.get_all_study_sessions") as mock_get_all:
        mock_get_all.return_value = sample
        response = client.get("/api/history")

    assert response.status_code == 200
    assert response.json() == {"sessions": sample}


def test_fetch_all_history_returns_empty_list(client):
    with patch("app.routes.history.get_all_study_sessions") as mock_get_all:
        mock_get_all.return_value = []
        response = client.get("/api/history")

    assert response.status_code == 200
    assert response.json() == {"sessions": []}


def test_fetch_history_item_returns_session(client):
    item = {
        "id": "abc123",
        "input_text": "Photosynthesis notes",
        "summary": "A summary",
        "quiz_json": [],
        "flashcards_json": [],
        "created_at": "2026-04-04T10:00:00Z",
    }

    with patch("app.routes.history.get_study_session_by_id") as mock_get_item:
        mock_get_item.return_value = item
        response = client.get("/api/history/abc123")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "abc123"
    assert body["input_text"] == "Photosynthesis notes"


def test_fetch_history_item_returns_404_when_not_found(client):
    with patch("app.routes.history.get_study_session_by_id") as mock_get_item:
        mock_get_item.return_value = None
        response = client.get("/api/history/missing-id")

    assert response.status_code == 404
    assert response.json() == {"detail": "Study session not found"}
