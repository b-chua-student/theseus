import pytest


@pytest.fixture
def project_payload():
    return {
        "project_name": "Test Project",
        "owner_name": "Test Owner",
        "owner_email": "owner@test.com",
    }


@pytest.fixture
def created_project(client, project_payload):
    client.post("/api/projects", json=project_payload)
    return project_payload
