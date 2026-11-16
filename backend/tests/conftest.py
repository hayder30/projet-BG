import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture()
def db_session():
    """A fresh in-memory SQLite database for every test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    session = Session()
    session.add_all(
        [
            User(username="admin", hashed_password=hash_password("admin123"), role="admin"),
            User(username="staff", hashed_password=hash_password("staff123"), role="staff"),
        ]
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # NOTE: no "with" block -> startup/seed code is not run in tests
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client):
    return _login(client, "admin", "admin123")


@pytest.fixture()
def staff_headers(client):
    return _login(client, "staff", "staff123")


@pytest.fixture()
def product(client, admin_headers):
    res = client.post(
        "/api/products",
        headers=admin_headers,
        json={"sku": "BG-001", "name": "Glow Serum", "price": 50, "cost": 25,
              "quantity": 10, "low_stock_threshold": 3},
    )
    assert res.status_code == 201, res.text
    return res.json()
