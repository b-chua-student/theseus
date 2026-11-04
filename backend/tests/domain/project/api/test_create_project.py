def test_create_project_returns_201(client, registered_user, project_payload) -> None:
    client.post(
        "/api/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    response = client.post("/api/projects", json=project_payload)

    assert response.status_code == 201


def test_create_project_unauthenticated_returns_401(client, project_payload) -> None:
    response = client.post("/api/projects", json=project_payload)

    assert response.status_code == 401


def test_create_project_missing_fields_returns_400(client, registered_user) -> None:
    client.post(
        "/api/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    response = client.post("/api/projects", json={})

    assert response.status_code == 400
