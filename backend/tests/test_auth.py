from app.models import Role
from tests.conftest import PASSWORD, auth_headers, login


def test_register_creates_regular_user(client):
    r = client.post("/api/auth/register", json={"email": "A@Example.com", "full_name": "Ann", "password": PASSWORD})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "a@example.com"
    assert body["role"] == "user"
    assert "hashed_password" not in body and "password" not in body


def test_register_cannot_self_assign_admin(client):
    r = client.post("/api/auth/register",
                    json={"email": "evil@example.com", "full_name": "Eve", "password": PASSWORD, "role": "admin"})
    assert r.status_code == 201
    assert r.json()["role"] == "user"


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "full_name": "Dup", "password": PASSWORD}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_register_rejects_short_password_and_bad_email(client):
    assert client.post("/api/auth/register",
                       json={"email": "x@example.com", "full_name": "X", "password": "short"}).status_code == 422
    assert client.post("/api/auth/register",
                       json={"email": "not-an-email", "full_name": "X", "password": PASSWORD}).status_code == 422


def test_login_success_and_me(client, make_user):
    make_user("u@example.com")
    r = login(client, "u@example.com")
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "u@example.com"


def test_login_wrong_password_and_unknown_email(client, make_user):
    make_user("u@example.com")
    assert login(client, "u@example.com", "wrong-password").status_code == 401
    assert login(client, "nobody@example.com").status_code == 401


def test_password_is_hashed_in_db(client, make_user, session_factory):
    make_user("u@example.com")
    from app.models import User
    with session_factory() as db:
        stored = db.query(User).one().hashed_password
    assert stored != PASSWORD and stored.startswith("$2")


def test_protected_endpoints_require_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/documents").status_code == 401
    assert client.get("/api/admin/users").status_code == 401


def test_invalid_and_tampered_token_rejected(client, make_user):
    make_user("u@example.com")
    token = login(client, "u@example.com").json()["access_token"]
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401


def test_deactivated_user_cannot_login_or_reuse_token(client, make_user, session_factory):
    uid = make_user("u@example.com")
    headers = auth_headers(client, "u@example.com")
    from app.models import User
    with session_factory() as db:
        db.get(User, uid).is_active = False
        db.commit()
    assert login(client, "u@example.com").status_code == 403
    assert client.get("/api/auth/me", headers=headers).status_code == 403
