from unittest.mock import patch


def test_rejects_non_pdf_filename(client, sample_pdf_bytes):
    response = client.post(
        "/api/upload",
        files={"file": ("not_a_pdf.txt", sample_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported"


def test_rejects_wrong_content_type(client, sample_pdf_bytes):
    response = client.post(
        "/api/upload",
        files={"file": ("file.pdf", sample_pdf_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid file type. Please upload a PDF"


def test_rejects_empty_file(client):
    response = client.post(
        "/api/upload",
        files={"file": ("file.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


def test_extraction_failure_returns_400(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_pdf", side_effect=Exception("boom")):
        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Failed to extract text from PDF"


def test_no_extracted_text_returns_400(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_pdf", return_value=""):
        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "No text could be extracted from PDF"


def test_study_material_generation_failure_returns_500(client, sample_pdf_bytes):
    with patch("app.routes.upload.extract_text_from_pdf", return_value="some extracted text"), \
         patch("app.routes.upload.generate_study_materials", side_effect=Exception("boom")):
        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to generate study materials"


def test_success_returns_materials_and_session_id(client, sample_pdf_bytes, sample_materials):
    with patch("app.routes.upload.extract_text_from_pdf", return_value="extracted text"), \
         patch("app.routes.upload.generate_study_materials", return_value=sample_materials), \
         patch("app.routes.upload.save_study_session", return_value=[{"id": "sess-123"}]) as mock_save:

        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["session_id"] == "sess-123"
    assert body["filename"] == "file.pdf"
    assert body["summary"] == sample_materials["summary"]
    assert body["quiz"] == sample_materials["quiz"]
    assert body["flashcards"] == sample_materials["flashcards"]

    mock_save.assert_called_once_with(
        "extracted text",
        summary=sample_materials["summary"],
        quiz=sample_materials["quiz"],
        flashcards=sample_materials["flashcards"],
        filename="file.pdf",
    )


def test_success_returns_materials_when_save_fails(client, sample_pdf_bytes, sample_materials):
    with patch("app.routes.upload.extract_text_from_pdf", return_value="extracted text"), \
         patch("app.routes.upload.generate_study_materials", return_value=sample_materials), \
         patch("app.routes.upload.save_study_session", side_effect=Exception("db fail")):

        response = client.post(
            "/api/upload",
            files={"file": ("file.pdf", sample_pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["session_id"] is None
    assert body["summary"] == sample_materials["summary"]
    assert body["filename"] == "file.pdf"
