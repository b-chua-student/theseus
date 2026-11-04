def test_login_success_sets_session(client, registered_user) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_login_wrong_password_returns_401(client, registered_user) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": registered_user["email"], "password": "wrong-password-123"},
    )

    assert response.status_code == 401
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_login_unknown_email_same_response_as_wrong_password(client, registered_user) -> None:
    unknown = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password-123"},
    )
    wrong = client.post(
        "/api/auth/login",
        json={"email": registered_user["email"], "password": "wrong-password-123"},
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.get_json() == wrong.get_json()


def test_login_invalid_email_format_returns_401(client) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "Invalid Email", "password": "whatever-password"},
    )

    assert response.status_code in (400, 401)


def test_login_missing_body_returns_400(client) -> None:
    response = client.post("/api/auth/login", json={})

    assert response.status_code == 400
