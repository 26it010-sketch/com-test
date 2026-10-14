from app.models import Role
from tests.conftest import auth_headers, login, upload


def test_regular_user_cannot_use_any_admin_endpoint(client, make_user):
    make_user("a@example.com")
    uid = make_user("b@example.com")
    h = auth_headers(client, "a@example.com")
    doc_id = upload(client, auth_headers(client, "b@example.com")).json()["id"]

    assert client.get("/api/admin/users", headers=h).status_code == 403
    assert client.get("/api/admin/documents", headers=h).status_code == 403
    assert client.get(f"/api/admin/users/{uid}/documents", headers=h).status_code == 403
    assert client.get(f"/api/admin/documents/{doc_id}/file", headers=h).status_code == 403
    assert client.delete(f"/api/admin/documents/{doc_id}", headers=h).status_code == 403
    assert client.patch(f"/api/admin/users/{uid}", headers=h, json={"is_active": False}).status_code == 403


def test_user_cannot_promote_self_by_editing_requests(client, make_user):
    uid = make_user("a@example.com")
    h = auth_headers(client, "a@example.com")
    assert client.patch(f"/api/admin/users/{uid}", headers=h, json={"is_active": True, "role": "admin"}).status_code == 403
    assert client.get("/api/auth/me", headers=h).json()["role"] == "user"


def test_admin_lists_users_with_document_counts(client, make_user):
    make_user("admin@example.com", Role.admin)
    make_user("a@example.com")
    upload(client, auth_headers(client, "a@example.com"))
    upload(client, auth_headers(client, "a@example.com"))
    users = client.get("/api/admin/users", headers=auth_headers(client, "admin@example.com")).json()
    counts = {u["email"]: u["document_count"] for u in users}
    assert counts == {"admin@example.com": 0, "a@example.com": 2}


def test_admin_sees_all_documents_with_owner_and_timestamp(client, make_user):
    make_user("admin@example.com", Role.admin)
    make_user("a@example.com")
    make_user("b@example.com")
    upload(client, auth_headers(client, "a@example.com"), name="a.pdf")
    upload(client, auth_headers(client, "b@example.com"), name="b.pdf")
    docs = client.get("/api/admin/documents", headers=auth_headers(client, "admin@example.com")).json()
    assert {d["original_filename"]: d["owner"]["email"] for d in docs} == {"a.pdf": "a@example.com", "b.pdf": "b@example.com"}
    assert all(d["uploaded_at"] for d in docs)


def test_admin_can_filter_by_user_view_and_delete_any_document(client, make_user):
    make_user("admin@example.com", Role.admin)
    uid = make_user("a@example.com")
    ha = auth_headers(client, "a@example.com")
    admin_h = auth_headers(client, "admin@example.com")
    doc_id = upload(client, ha).json()["id"]

    assert [d["id"] for d in client.get(f"/api/admin/users/{uid}/documents", headers=admin_h).json()] == [doc_id]
    assert client.get(f"/api/admin/documents/{doc_id}/file", headers=admin_h).status_code == 200
    assert client.delete(f"/api/admin/documents/{doc_id}", headers=admin_h).status_code == 204
    assert client.get("/api/documents", headers=ha).json() == []
    assert client.delete(f"/api/admin/documents/{doc_id}", headers=admin_h).status_code == 404


def test_admin_can_deactivate_and_reactivate_user(client, make_user):
    make_user("admin@example.com", Role.admin)
    uid = make_user("a@example.com")
    ha = auth_headers(client, "a@example.com")
    admin_h = auth_headers(client, "admin@example.com")

    r = client.patch(f"/api/admin/users/{uid}", headers=admin_h, json={"is_active": False})
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert client.get("/api/documents", headers=ha).status_code == 403  # existing token stops working
    assert login(client, "a@example.com").status_code == 403

    client.patch(f"/api/admin/users/{uid}", headers=admin_h, json={"is_active": True})
    assert login(client, "a@example.com").status_code == 200


def test_admin_cannot_deactivate_self(client, make_user):
    aid = make_user("admin@example.com", Role.admin)
    h = auth_headers(client, "admin@example.com")
    assert client.patch(f"/api/admin/users/{aid}", headers=h, json={"is_active": False}).status_code == 400


def test_admin_user_not_found(client, make_user):
    make_user("admin@example.com", Role.admin)
    h = auth_headers(client, "admin@example.com")
    assert client.patch("/api/admin/users/9999", headers=h, json={"is_active": False}).status_code == 404
    assert client.get("/api/admin/users/9999/documents", headers=h).status_code == 404
