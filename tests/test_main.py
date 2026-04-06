def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "app": "Quizly"}


def test_home_returns_index(client):
    resp = client.get("/")
    # FileResponse should return the index.html content
    assert resp.status_code == 200
    # quick sanity check that page title or app name appears
    assert "Quizly" in resp.text


def test_static_asset_served(client):
    resp = client.get("/static/styles.css")
    assert resp.status_code == 200
    ctype = resp.headers.get("content-type", "")
    assert "text/css" in ctype
