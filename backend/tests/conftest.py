import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models import Role, User

PASSWORD = "correct-horse-battery"
PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


@pytest.fixture()
def session_factory():
    # In-memory SQLite keeps tests fast and independent of a running PostgreSQL.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False)
    engine.dispose()


@pytest.fixture()
def client(session_factory, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(client, session_factory):
    """Creates a user directly in the DB and returns auth headers + the user id."""
    def _make(email, role=Role.user, active=True):
        with session_factory() as db:
            user = User(email=email, full_name=email.split("@")[0], role=role,
                        hashed_password=hash_password(PASSWORD), is_active=active)
            db.add(user)
            db.commit()
            user_id = user.id
        return user_id

    return _make


def login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", data={"username": email, "password": password})


def auth_headers(client, email):
    token = login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload(client, headers, name="report.pdf", content=PDF_BYTES, content_type="application/pdf"):
    return client.post("/api/documents", headers=headers, files={"file": (name, content, content_type)})
