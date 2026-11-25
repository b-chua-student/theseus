"""Run the same identity contracts against isolated database namespaces."""

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

from domain.identity.infrastructure.adapters.argon_password_hasher import ArgonPasswordHasher
from domain.identity.infrastructure.adapters.in_memory_identity_repository import (
    InMemoryIdentityRepository,
)
from domain.identity.infrastructure.adapters.mongodb_identity_repository import (
    MongoIdentityRepository,
)
from domain.identity.infrastructure.ports.identity_repository import (
    IdentityConflict,
    IdentityRepository,
)
from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import DisplayName, Email, UserId
from domain.identity.services.auth.login_user import LoginUserService


@pytest.fixture(params=["memory", "mongo", "postgres"])
def repo(request) -> Iterator[IdentityRepository]:
    if request.param == "memory":
        yield InMemoryIdentityRepository()
    elif request.param == "mongo":
        uri = os.getenv("TEST_MONGODB_URI")
        if not uri:
            pytest.skip("Set TEST_MONGODB_URI to exercise MongoDB")
            return
        adapter = MongoIdentityRepository(uri, "theseus_tests", collection=uuid4().hex)
        try:
            yield adapter
        finally:
            adapter.users.drop()
            adapter.close()
    else:
        dsn = os.getenv("TEST_POSTGRES_DSN")
        if not dsn:
            pytest.skip("Set TEST_POSTGRES_DSN to exercise PostgreSQL")
        import psycopg
        from psycopg.conninfo import make_conninfo

        from domain.identity.infrastructure.adapters.postgreqsql_identity_repository import (
            PostgresIdentityRepository,
        )

        schema = "test_" + uuid4().hex
        with psycopg.connect(dsn, autocommit=True) as admin:
            admin.execute(f"CREATE SCHEMA {schema}")
            postgres = PostgresIdentityRepository(
                make_conninfo(dsn, options=f"-csearch_path={schema}")
            )
            try:
                yield postgres
            finally:
                postgres.close()
                admin.execute(f"DROP SCHEMA {schema} CASCADE")


def account(email) -> User:
    return User(UserId.new(), DisplayName("Reader"), Email(email), None)


@pytest.mark.parametrize("same_subject", [True, False])
def test_concurrent_provision(repo, same_subject) -> None:
    barrier = Barrier(2)

    def attempt(i) -> UserId | None:
        subject = "same" if same_subject else str(i)
        candidate = account("Same@example.com")
        barrier.wait(timeout=5)
        try:
            repo.provision(candidate, "issuer", subject)
            return candidate.id
        except IdentityConflict:
            committed = repo.find_identity("issuer", subject)
            return committed.id if committed else None

    with ThreadPoolExecutor(2) as pool:
        ids = list(pool.map(attempt, range(2)))
    owner = repo.get_by_email(Email("same@example.com"))
    assert ids.count(owner.id) == (2 if same_subject else 1)
    assert ids.count(None) == (0 if same_subject else 1)


def test_link_conflict_and_passwordless_reload(repo) -> None:
    first, second = account("first@example.com"), account("second@example.com")
    repo.provision(first, "issuer", "first")
    repo.provision(second, "issuer", "second")
    with pytest.raises(IdentityConflict):
        repo.link(second, "issuer", "first")
    assert repo.find_identity("issuer", "first") == first
    assert repo.find_identity("issuer", "second") == second
    assert repo.get_by_id(first.id).password_hash is None


def test_migrate_legacy_password_users() -> None:
    from pymongo import MongoClient

    from domain.identity.services.auth.register_user import RegisterUserService

    uri = os.getenv("TEST_MONGODB_URI")
    if not uri:
        pytest.skip("Set TEST_MONGODB_URI to exercise migration")
        return
    hasher = ArgonPasswordHasher()
    users = [account(f"Legacy{i}@example.com") for i in range(2)]
    password = hasher.hash("test-password")
    with MongoClient[dict](uri) as client:
        collection = client.theseus_tests[uuid4().hex]
        try:
            for user in users:
                collection.insert_one(
                    {
                        "_id": str(user.id.value),
                        "email": user.email.value,
                        "display_name": "Reader",
                        "password_hash": password,
                    }
                )
            for _ in range(2):
                repo = MongoIdentityRepository(uri, "theseus_tests", collection=collection.name)
                repo.close()
            repo = MongoIdentityRepository(uri, "theseus_tests", collection=collection.name)
            try:
                users.append(
                    RegisterUserService(repo, hasher).execute(
                        "New", "new@example.com", "test-password"
                    )
                )
                for user in users:
                    found = LoginUserService(repo, hasher).execute(
                        user.email.value, "test-password"
                    )
                    assert found.id == user.id
            finally:
                repo.close()
        finally:
            collection.drop()


def test_two_callbacks_cannot_claim_the_same_pending_request(repo) -> None:
    from bootstrap.app import create_app
    from bootstrap.container import build_container

    app = create_app({"TESTING": True}, build_container(identity_repo=repo))
    store = app.extensions["oauth_attempts"]
    key = store.put({"state": "unique-attempt"})
    with ThreadPoolExecutor(2) as pool:
        outcomes = list(pool.map(store.take, (key, key)))
    assert sum(result is not None for result in outcomes) == 1
    assert next(result for result in outcomes if result)["state"] == "unique-attempt"


def test_identity_conflict_rolls_back_new_email(repo) -> None:
    first, concurrent = account("first@example.com"), account("changed@example.com")
    repo.provision(first, "issuer", "subject")
    with pytest.raises(IdentityConflict):
        repo.provision(concurrent, "issuer", "subject")
    assert repo.find_identity("issuer", "subject") == first
    assert repo.get_by_email(concurrent.email) is None
