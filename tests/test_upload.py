from unittest.mock import patch


def test_rejects_unsupported_filename(client, sample_pdf_bytes):
    response = client.post(
        "/api/upload",
        files={"file": ("not_a_pdf.txt", sample_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF, DOCX, and PPTX files are supported"


def test_rejects_empty_file(client):
    response = client.post(
        "/api/upload",
        files={"file": ("file.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_extraction_failure_returns_400(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_upload", side_effect=Exception("boom")):
        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Failed to extract text from file"


def test_no_extracted_text_returns_400(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_upload", return_value=""):
        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "No text could be extracted from file"


def test_upload_success_returns_upload_id(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_upload", return_value="extracted text"):
        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["filename"] == "file.pdf"
    assert body["upload_id"]
    assert set(body["actions"]) == {"summary", "quiz", "flashcards"}


def test_generate_requires_upload_id(client):
    response = client.post(
        "/api/upload/generate",
        json={"upload_id": "", "action": "summary"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "upload_id is required"


def test_generate_rejects_invalid_action(client):
    response = client.post(
        "/api/upload/generate",
        json={"upload_id": "abc", "action": "invalid"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "action must be one of: summary, quiz, flashcards"


def test_generate_rejects_missing_upload(client):
    response = client.post(
        "/api/upload/generate",
        json={"upload_id": "missing", "action": "summary"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Upload not found or expired"


def test_generate_summary_success(client, sample_pdf_bytes, sample_materials):
    with patch("app.routes.upload.extract_text_from_upload", return_value="extracted text"):
        upload_response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    upload_id = upload_response.json()["upload_id"]

    with patch("app.routes.upload.generate_study_materials", return_value=sample_materials), \
         patch("app.routes.upload.save_study_session", return_value=[{"id": "sess-123"}]):
        response = client.post(
            "/api/upload/generate",
            json={"upload_id": upload_id, "action": "summary"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["session_id"] == "sess-123"
    assert body["action"] == "summary"
    assert body["summary"] == sample_materials["summary"]
    assert body["quiz"] == []
    assert body["flashcards"] == []


def test_generate_quiz_success(client, sample_pdf_bytes, sample_materials):
    with patch("app.routes.upload.extract_text_from_upload", return_value="extracted text"):
        upload_response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    upload_id = upload_response.json()["upload_id"]

    with patch("app.routes.upload.generate_study_materials", return_value=sample_materials), \
         patch("app.routes.upload.save_study_session", return_value=[{"id": "sess-789"}]):
        response = client.post(
            "/api/upload/generate",
            json={"upload_id": upload_id, "action": "quiz"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "quiz"
    assert body["summary"] == ""
    assert body["quiz"] == sample_materials["quiz"]
    assert body["flashcards"] == []


def test_generation_failure_returns_500(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_upload", return_value="some extracted text"):
        upload_response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    upload_id = upload_response.json()["upload_id"]

    with patch("app.routes.upload.generate_study_materials", side_effect=Exception("boom")):
        response = client.post(
            "/api/upload/generate",
            json={"upload_id": upload_id, "action": "summary"},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to generate study materials"


def test_generate_flashcards_enforces_even_count(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_upload", return_value="extracted text"):
        upload_response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    upload_id = upload_response.json()["upload_id"]
    odd_materials = {
        "summary": "",
        "quiz": [],
        "flashcards": [
            {"term": "T1", "definition": "D1"},
            {"term": "T2", "definition": "D2"},
            {"term": "T3", "definition": "D3"},
        ],
    }

    with patch("app.routes.upload.generate_study_materials", return_value=odd_materials), \
         patch("app.routes.upload.save_study_session", return_value=[{"id": "sess-456"}]):
        response = client.post(
            "/api/upload/generate",
            json={"upload_id": upload_id, "action": "flashcards"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "flashcards"
    assert len(body["flashcards"]) % 2 == 0
