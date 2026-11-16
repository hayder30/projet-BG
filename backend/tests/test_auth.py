def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["user"]["role"] == "admin"


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert res.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/products").status_code == 401


def test_invalid_token_rejected(client):
    res = client.get("/api/products", headers={"Authorization": "Bearer garbage"})
    assert res.status_code == 401


def test_me(client, staff_headers):
    res = client.get("/api/auth/me", headers=staff_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "staff"


def test_admin_can_create_user(client, admin_headers):
    res = client.post(
        "/api/auth/users",
        headers=admin_headers,
        json={"username": "newbie", "password": "secret123", "role": "staff"},
    )
    assert res.status_code == 201
    assert "hashed_password" not in res.json()
    # the new user can log in
    login = client.post("/api/auth/login", json={"username": "newbie", "password": "secret123"})
    assert login.status_code == 200


def test_staff_cannot_create_user(client, staff_headers):
    res = client.post(
        "/api/auth/users",
        headers=staff_headers,
        json={"username": "hacker", "password": "secret123"},
    )
    assert res.status_code == 403


def test_duplicate_username(client, admin_headers):
    res = client.post(
        "/api/auth/users",
        headers=admin_headers,
        json={"username": "staff", "password": "secret123"},
    )
    assert res.status_code == 409
