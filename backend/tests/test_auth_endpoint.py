from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_admin_login_and_me():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["role"] == "admin"
    assert payload["access_token"].startswith("demo-token:")

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["user_id"] == "admin"


def test_worker_login_and_user_list():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "worker_ahu", "password": "worker123"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "worker"

    users = client.get("/api/v1/auth/users")
    assert users.status_code == 200
    assert any(item["user_id"] == "worker_chiller" for item in users.json()["items"])


def test_login_rejects_invalid_password():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401
