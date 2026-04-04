import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient for the whole test session."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_bytes():
    """Small deterministic byte string to represent an uploaded PDF file in tests.

    Note: the app's PDF extractor should be patched by tests that need to control
    the extracted text; this fixture only provides a consistent file payload.
    """
    return b"%PDF-1.4\n%fake pdf content\n"


@pytest.fixture
def sample_materials():
    """Small sample study materials useful for assertions.

    Tests should patch Gemini to return these values when needed.
    """
    return {
        "summary": "This is a concise study summary.",
        "quiz": [
            {"question": "Q1", "options": ["A", "B", "C", "D"], "answer": "A"}
        ],
        "flashcards": [{"term": "T1", "definition": "D1"}],
    }
