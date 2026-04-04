from unittest.mock import patch


def test_empty_topic_returns_400(client):
    response = client.post("/api/quiz/generate", json={"topic": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Topic cannot be empty."}


def test_success_returns_quiz(client):
    sample_quiz = [
        {"question": "What is photosynthesis?", "options": ["A", "B", "C", "D"], "answer": "A"}
    ]

    with patch("app.routes.quiz.generate_quiz_from_topic", return_value=sample_quiz):
        response = client.post("/api/quiz/generate", json={"topic": "Photosynthesis"})

    assert response.status_code == 200
    assert response.json() == {"quiz": sample_quiz}


def test_generation_failure_returns_500(client):
    with patch("app.routes.quiz.generate_quiz_from_topic", return_value=None):
        response = client.post("/api/quiz/generate", json={"topic": "Anything"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to generate quiz for the given topic."}
