from app.core.config import settings
from tests.conftest import PDF_BYTES, auth_headers, upload


def test_user_can_upload_list_view_and_delete_own_document(client, make_user):
    make_user("a@example.com")
    h = auth_headers(client, "a@example.com")

    r = upload(client, h)
    assert r.status_code == 201
    doc = r.json()
    assert doc["original_filename"] == "report.pdf" and doc["size_bytes"] == len(PDF_BYTES)

    listing = client.get("/api/documents", headers=h).json()
    assert [d["id"] for d in listing] == [doc["id"]]

    f = client.get(f"/api/documents/{doc['id']}/file", headers=h)
    assert f.status_code == 200
    assert f.headers["content-type"] == "application/pdf"
    assert f.content == PDF_BYTES

    assert client.delete(f"/api/documents/{doc['id']}", headers=h).status_code == 204
    assert client.get("/api/documents", headers=h).json() == []
    assert client.get(f"/api/documents/{doc['id']}/file", headers=h).status_code == 404


def test_files_are_stored_under_random_names(client, make_user, tmp_path):
    make_user("a@example.com")
    h = auth_headers(client, "a@example.com")
    upload(client, h, name="../../etc/passwd.pdf")
    stored = list((tmp_path / "uploads").iterdir())
    assert len(stored) == 1 and stored[0].name != "passwd.pdf" and stored[0].suffix == ".pdf"


def test_user_cannot_access_another_users_document(client, make_user):
    make_user("a@example.com")
    make_user("b@example.com")
    ha, hb = auth_headers(client, "a@example.com"), auth_headers(client, "b@example.com")
    doc_id = upload(client, ha).json()["id"]

    # B sees nothing in their list and gets 404 (not 403) for A's document on every route.
    assert client.get("/api/documents", headers=hb).json() == []
    assert client.get(f"/api/documents/{doc_id}", headers=hb).status_code == 404
    assert client.get(f"/api/documents/{doc_id}/file", headers=hb).status_code == 404
    assert client.delete(f"/api/documents/{doc_id}", headers=hb).status_code == 404

    # ...and A's document is untouched.
    assert client.get(f"/api/documents/{doc_id}/file", headers=ha).status_code == 200


def test_unauthenticated_cannot_download_or_upload(client, make_user):
    make_user("a@example.com")
    doc_id = upload(client, auth_headers(client, "a@example.com")).json()["id"]
    assert client.get(f"/api/documents/{doc_id}/file").status_code == 401
    assert client.delete(f"/api/documents/{doc_id}").status_code == 401
    assert client.post("/api/documents", files={"file": ("x.pdf", PDF_BYTES, "application/pdf")}).status_code == 401


def test_rejects_non_pdf_extension(client, make_user):
    make_user("a@example.com")
    h = auth_headers(client, "a@example.com")
    assert upload(client, h, name="notes.txt", content=PDF_BYTES).status_code == 400


def test_rejects_wrong_content_type(client, make_user):
    make_user("a@example.com")
    h = auth_headers(client, "a@example.com")
    assert upload(client, h, content_type="text/html").status_code == 400


def test_rejects_file_that_is_not_really_a_pdf(client, make_user):
    make_user("a@example.com")
    h = auth_headers(client, "a@example.com")
    r = upload(client, h, name="fake.pdf", content=b"<html><script>alert(1)</script></html>")
    assert r.status_code == 400
    assert client.get("/api/documents", headers=h).json() == []


def test_rejects_oversized_file_and_cleans_up(client, make_user, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    make_user("a@example.com")
    h = auth_headers(client, "a@example.com")
    big = PDF_BYTES + b"0" * (1024 * 1024 + 10)
    assert upload(client, h, content=big).status_code == 413
    assert client.get("/api/documents", headers=h).json() == []
    assert list((tmp_path / "uploads").iterdir()) == []


def test_nonexistent_document_returns_404(client, make_user):
    make_user("a@example.com")
    h = auth_headers(client, "a@example.com")
    assert client.get("/api/documents/9999/file", headers=h).status_code == 404
