from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_export_csv_returns_csv_file():
    response = client.get("/api/v1/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_export_csv_has_content_disposition():
    response = client.get("/api/v1/export/csv")
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "energy_records" in disposition


def test_export_csv_contains_header_row():
    response = client.get("/api/v1/export/csv")
    first_line = response.text.strip().split("\n")[0]
    assert "record_id" in first_line
    assert "building_id" in first_line
    assert "electricity_kwh" in first_line


def test_export_csv_with_building_filter():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get("/api/v1/export/csv", params={"building_id": building_id})
    assert response.status_code == 200
    lines = response.text.strip().split("\n")
    # All data rows should belong to the filtered building
    for line in lines[1:]:
        if line.strip():
            assert building_id in line


def test_export_csv_filename_includes_building_id():
    buildings = client.get("/api/v1/buildings").json()["items"]
    building_id = buildings[0]["building_id"]
    response = client.get("/api/v1/export/csv", params={"building_id": building_id})
    disposition = response.headers.get("content-disposition", "")
    assert building_id in disposition
