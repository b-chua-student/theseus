def test_register_returns_201_and_sets_session(client, user_payload) -> None:
    response = client.post("/api/auth/register", json=user_payload)

    assert response.status_code == 201
    assert response.get_json()["display_name"] == user_payload["display_name"]
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_register_does_not_leak_password(client, user_payload) -> None:
    response = client.post("/api/auth/register", json=user_payload)

    body = response.get_data(as_text=True)
    assert user_payload["password"] not in body
    assert "password_hash" not in body


def test_register_duplicate_email_returns_409(client, user_payload) -> None:
    client.post("/api/auth/register", json=user_payload)

    response = client.post("/api/auth/register", json=user_payload)

    assert response.status_code == 409


def test_register_weak_password_returns_error(client, user_payload) -> None:
    user_payload["password"] = "short"

    response = client.post("/api/auth/register", json=user_payload)

    assert response.status_code in (400, 422)


def test_register_invalid_email_returns_400(client, user_payload) -> None:
    user_payload["email"] = "Invalid Email"

    response = client.post("/api/auth/register", json=user_payload)

    assert response.status_code == 400


def test_register_missing_fields_returns_400(client) -> None:
    response = client.post("/api/auth/register", json={})

    assert response.status_code == 400
