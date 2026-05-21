import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app


@pytest.fixture()
def auth_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_register_login_and_me(auth_client: TestClient):
    reg = auth_client.post(
        "/auth/register",
        json={
            "email": "student@example.com",
            "password": "secret12",
            "display_name": "Иван",
        },
    )
    assert reg.status_code == 200
    reg_body = reg.json()
    assert reg_body["email"] == "student@example.com"
    assert reg_body["display_name"] == "Иван"
    assert reg_body["user_id"]
    assert reg_body["access_token"]

    reg_no_name = auth_client.post(
        "/auth/register",
        json={"email": "noname@example.com", "password": "secret12"},
    )
    assert reg_no_name.status_code == 200
    assert reg_no_name.json()["display_name"] is None

    dup = auth_client.post(
        "/auth/register",
        json={"email": "student@example.com", "password": "otherpass"},
    )
    assert dup.status_code == 400
    assert dup.json()["code"] == "email_taken"

    bad = auth_client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "wrong"},
    )
    assert bad.status_code == 401

    login = auth_client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "secret12"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"
    assert me.json()["display_name"] == "Иван"
