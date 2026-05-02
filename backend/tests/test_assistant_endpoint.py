from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_assistant_query_returns_answer():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "当前有哪些建筑？"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert isinstance(payload["citations"], list)
    assert isinstance(payload["follow_up"], list)


def test_assistant_query_about_anomalies():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "当前有哪些异常记录？"},
    )
    assert response.status_code == 200
    assert response.json()["answer"]


def test_assistant_query_about_cop():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "COP 能效怎么样？"},
    )
    assert response.status_code == 200
    assert response.json()["answer"]


def test_assistant_query_about_energy():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "总电耗是多少？"},
    )
    assert response.status_code == 200
    assert response.json()["answer"]


def test_assistant_query_default_response():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "你好，随便聊聊"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert len(payload["citations"]) >= 1

