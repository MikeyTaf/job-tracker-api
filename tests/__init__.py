import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Test database - separate from your real one so tests never touch your actual data
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/job_tracker_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---- CREATE ----

def test_create_application():
    response = client.post("/applications/", json={
        "company": "Google",
        "job_title": "Backend Engineer",
        "status": "applied",
        "tags": ["backend", "remote"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["company"] == "Google"
    assert data["job_title"] == "Backend Engineer"
    assert data["status"] == "applied"
    assert data["tags"] == ["backend", "remote"]
    assert "id" in data
    assert "created_at" in data


def test_create_application_missing_company():
    response = client.post("/applications/", json={
        "job_title": "Backend Engineer",
    })
    assert response.status_code == 422


def test_create_application_empty_company():
    response = client.post("/applications/", json={
        "company": "",
        "job_title": "Backend Engineer",
    })
    assert response.status_code == 422


# ---- READ ----

def test_list_applications_empty():
    response = client.get("/applications/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_applications():
    client.post("/applications/", json={"company": "Google", "job_title": "SWE"})
    client.post("/applications/", json={"company": "Meta", "job_title": "SWE"})

    response = client.get("/applications/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_application():
    create_response = client.post("/applications/", json={
        "company": "Stripe",
        "job_title": "Backend Engineer",
    })
    app_id = create_response.json()["id"]

    response = client.get(f"/applications/{app_id}")
    assert response.status_code == 200
    assert response.json()["company"] == "Stripe"


def test_get_application_not_found():
    response = client.get("/applications/9999")
    assert response.status_code == 404


# ---- FILTER ----

def test_filter_by_status():
    client.post("/applications/", json={"company": "Google", "job_title": "SWE", "status": "applied"})
    client.post("/applications/", json={"company": "Meta", "job_title": "SWE", "status": "rejected"})

    response = client.get("/applications/?status=applied")
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == "Google"


def test_filter_by_tag():
    client.post("/applications/", json={"company": "Google", "job_title": "SWE", "tags": ["backend"]})
    client.post("/applications/", json={"company": "Meta", "job_title": "SWE", "tags": ["frontend"]})

    response = client.get("/applications/?tag=backend")
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == "Google"


# ---- UPDATE ----

def test_update_application():
    create_response = client.post("/applications/", json={
        "company": "Google",
        "job_title": "SWE",
        "status": "applied",
    })
    app_id = create_response.json()["id"]

    response = client.put(f"/applications/{app_id}", json={"status": "phone_screen"})
    assert response.status_code == 200
    assert response.json()["status"] == "phone_screen"
    assert response.json()["company"] == "Google"  # unchanged fields stay the same


def test_update_application_not_found():
    response = client.put("/applications/9999", json={"status": "rejected"})
    assert response.status_code == 404


# ---- DELETE ----

def test_delete_application():
    create_response = client.post("/applications/", json={
        "company": "Google",
        "job_title": "SWE",
    })
    app_id = create_response.json()["id"]

    response = client.delete(f"/applications/{app_id}")
    assert response.status_code == 204

    # Verify it's actually gone
    get_response = client.get(f"/applications/{app_id}")
    assert get_response.status_code == 404


def test_delete_application_not_found():
    response = client.delete("/applications/9999")
    assert response.status_code == 404


# ---- STATS ----

def test_stats_empty():
    response = client.get("/applications/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_applications"] == 0
    assert data["by_status"] == {}
    assert data["most_recent"] is None


def test_stats_with_data():
    client.post("/applications/", json={"company": "Google", "job_title": "SWE", "status": "applied"})
    client.post("/applications/", json={"company": "Meta", "job_title": "SWE", "status": "applied"})
    client.post("/applications/", json={"company": "Stripe", "job_title": "SWE", "status": "rejected"})

    response = client.get("/applications/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_applications"] == 3
    assert data["by_status"]["applied"] == 2
    assert data["by_status"]["rejected"] == 1
