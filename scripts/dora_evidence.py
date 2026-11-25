"""Retrieve and validate API evidence for DORA reports."""

import json
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

SUCCESS = {"live", "deactivated"}
OTHER_STATUSES = {
    "created",
    "queued",
    "build_in_progress",
    "update_in_progress",
    "pre_deploy_in_progress",
    "build_failed",
    "update_failed",
    "pre_deploy_failed",
    "canceled",
}


class EvidenceError(Exception):
    """An evidence failure with a fixed, safe diagnostic."""


class NoRedirect(HTTPRedirectHandler):
    """Keep authorization headers on the original API host."""

    def redirect_request(self, *args: object, **kwargs: object) -> None:
        """Decline redirects."""
        return None


def request(url: str, token: str, source: str) -> tuple[list[Any], str]:
    """Fetch one JSON page without leaking request or response details."""
    try:
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if source == "GitHub":
            headers["X-GitHub-Api-Version"] = "2022-11-28"
        with build_opener(NoRedirect()).open(Request(url, headers=headers), timeout=30) as response:
            rows = json.load(response)
            if not isinstance(rows, list):
                raise ValueError
            return rows, response.headers.get("Link", "")
    except Exception:
        raise EvidenceError(f"{source} evidence request failed.") from None


def timestamp(value: str) -> datetime:
    """Parse an offset-aware API timestamp and normalize it to UTC."""
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError
    return result.astimezone(UTC)


def render_rows(service: str, token: str) -> Iterator[dict[str, Any]]:
    """Walk Render history through the final cursor."""
    endpoint = f"https://api.render.com/v1/services/{service}/deploys"
    query: dict[str, str] = {"limit": "100"}
    seen = set()
    for _ in range(10000):
        rows, _ = request(f"{endpoint}?{urlencode(query)}", token, "Render")
        if not rows:
            return
        for row in rows:
            yield row["deploy"]
        cursor = rows[-1]["cursor"]
        if not isinstance(cursor, str) or not cursor or cursor in seen:
            raise EvidenceError("Render deployment pagination evidence is invalid.")
        seen.add(cursor)
        query["cursor"] = cursor
    raise EvidenceError("Render deployment pagination did not terminate.")


def fetch_production_arrivals(
    service: str, token: str, first_id: str
) -> list[tuple[dict[str, Any], datetime]]:
    """Read the designated service and verify its independently confirmed history anchor."""
    deployments = []
    seen = set()
    oldest = datetime.max.replace(tzinfo=UTC)
    anchor = None
    try:
        for row in render_rows(service, token):
            deploy_id = row["id"]
            if not re.fullmatch(r"dep-[A-Za-z0-9]+", deploy_id) or deploy_id in seen:
                raise ValueError
            seen.add(deploy_id)
            created = timestamp(row["createdAt"])
            oldest = min(oldest, created)
            if deploy_id == first_id:
                anchor = created
            status = row["status"]
            if status in SUCCESS:
                live = timestamp(row["finishedAt"])
                if live < created:
                    raise ValueError
                deployments.append((row, live))
            elif status not in OTHER_STATUSES:
                raise ValueError
    except (KeyError, TypeError, ValueError):
        raise EvidenceError("Render deployment evidence is incomplete or invalid.") from None
    if not (anchor == oldest or (first_id == "empty" and not seen)):
        raise EvidenceError("Render history does not match the verified first deployment.")
    return deployments
