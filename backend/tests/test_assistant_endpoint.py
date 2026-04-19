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

