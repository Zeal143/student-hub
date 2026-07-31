"""Registration and login"""


def test_register_creates_account(client):
    res = client.post("/api/auth/register", json={
        "name": "Aoife Murphy",
        "email": "aoife@example.com",
        "password": "password123",
    })
    assert res.status_code == 201


def test_register_rejects_duplicate_email(client):
    payload = {"name": "Aoife Murphy", "email": "aoife@example.com", "password": "password123"}
    client.post("/api/auth/register", json=payload)

    res = client.post("/api/auth/register", json=payload)

    assert res.status_code == 409
    assert "already exists" in res.get_json()["error"]


def test_register_rejects_short_password(client):
    res = client.post("/api/auth/register", json={
        "name": "Aoife Murphy",
        "email": "aoife@example.com",
        "password": "short",
    })
    assert res.status_code == 400


def test_register_rejects_invalid_email(client):
    res = client.post("/api/auth/register", json={
        "name": "Aoife Murphy",
        "email": "not-an-email",
        "password": "password123",
    })
    assert res.status_code == 400


def test_login_succeeds_with_correct_credentials(client):
    client.post("/api/auth/register", json={
        "name": "Aoife Murphy", "email": "aoife@example.com", "password": "password123",
    })

    res = client.post("/api/auth/login", json={"email": "aoife@example.com", "password": "password123"})

    assert res.status_code == 200
    body = res.get_json()
    assert "access_token" in body
    assert body["user"]["email"] == "aoife@example.com"


def test_login_fails_with_wrong_password(client):
    client.post("/api/auth/register", json={
        "name": "Aoife Murphy", "email": "aoife@example.com", "password": "password123",
    })

    res = client.post("/api/auth/login", json={"email": "aoife@example.com", "password": "wrong-password"})

    assert res.status_code == 401


def test_me_requires_a_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["email"] == "student@example.com"
