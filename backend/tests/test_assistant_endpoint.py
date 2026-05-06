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


def test_assistant_query_about_maintenance():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "冷却塔应该多久维护一次？"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "冷却塔" in payload["answer"] or "维护" in payload["answer"]
    assert any("equipment_maintenance_playbook.md" in item["path"] for item in payload["citations"])


def test_assistant_query_about_building_type():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "为什么实验楼电耗这么高？"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "实验楼" in payload["answer"] or "科研实验楼" in payload["answer"]
    assert any("building_type_notes.md" in item["path"] for item in payload["citations"])


def test_assistant_query_about_data_sources():
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "这些数据是纯随机生成的吗？"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "纯随机" in payload["answer"] or "公开资料" in payload["answer"]
    assert any("data_quality_report_round1.md" in item["path"] for item in payload["citations"])

