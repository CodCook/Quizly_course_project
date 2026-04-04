from unittest.mock import patch


def test_empty_text_returns_400(client):
    response = client.post("/api/flashcards", json={"text": "   "})
    assert response.status_code == 400
    assert response.json() == {"detail": "Text is required"}


def test_success_returns_flashcards(client):
    sample_materials = {"flashcards": [{"term": "T1", "definition": "D1"}]}

    with patch("app.routes.flashcards.generate_study_materials", return_value=sample_materials):
        response = client.post("/api/flashcards", json={"text": "Learn math"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["flashcards"] == sample_materials["flashcards"]


def test_generation_failure_returns_500(client):
    with patch("app.routes.flashcards.generate_study_materials", side_effect=Exception("boom")):
        response = client.post("/api/flashcards", json={"text": "Some content"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to generate flashcards"}
