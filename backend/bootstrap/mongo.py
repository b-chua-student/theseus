"""MongoDB connection settings shared by every Mongo-backed repository."""

import os
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

DEFAULT_URI = "mongodb://localhost:27017"
DEFAULT_DB = "mydb"


def mongo_settings() -> tuple[str, str]:
    """Connection URI and database name, from MONGODB_URI / MONGODB_DB (with local defaults)."""
    load_dotenv()
    return os.getenv("MONGODB_URI", DEFAULT_URI), os.getenv("MONGODB_DB", DEFAULT_DB)


def create_database(uri: str | None = None, db_name: str | None = None) -> Database:
    """Open the application database.

    ``tz_aware=True`` makes pymongo return timezone-aware (UTC) datetimes, matching
    ``domain.shared.clock.now()``; without it, values read back would be naive and
    comparing them with freshly created ones would raise.
    """
    default_uri, default_db = mongo_settings()
    client: MongoClient[dict[str, Any]] = MongoClient(uri or default_uri, tz_aware=True)
    return client[db_name or default_db]
