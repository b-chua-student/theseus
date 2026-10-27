def test_list_manuscripts_returns_200_and_all_items(client, manuscript_repo) -> None:
    response = client.get("/api/manuscripts")

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
    assert len(response.get_json()) == len(manuscript_repo.get_all())


def test_list_manuscripts_returns_empty_list_when_none_exist(bare_app) -> None:
    response = bare_app.test_client().get("/api/manuscripts")

    assert response.status_code == 200
    assert response.get_json() == []
