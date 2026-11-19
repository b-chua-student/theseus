import math
import time
from datetime import datetime
from typing import Any
from uuid import UUID

from bootstrap.extensions import limiter
from domain.identity.api.auth.routes import login_required
from domain.shared.errors import DomainError
from flask import Blueprint, Response, current_app, jsonify, request, session
from flask.typing import ResponseReturnValue
from flask_limiter.errors import RateLimitExceeded
from pydantic import ValidationError

from domain.src_lib.models.aggregates import Source
from domain.src_lib.services.errors import SourceNotFound
from domain.src_lib.services.list_text_sources import TextSourcePage, snippet_of

from .errors import SourceNotFoundError
from .requests import AddSourceRequest, TextSourceRequest, UpdateSourceMetadataRequest

source_bp = Blueprint("source_library", __name__)


@source_bp.get("")
@login_required
def list_sources() -> ResponseReturnValue:
    """List all sources in the library."""
    container = current_app.extensions["container"]

    sources = container.source.list.execute()
    if request.args.get("projectId"):
        try:
            project_id = UUID(request.args["projectId"])
        except ValueError:
            return jsonify(error="Invalid projectId"), 400
        sources = [source for source in sources if source.project_id == project_id]

    return jsonify(
        [
            dict(
                id=str(s.id.value),
                kind=s.kind,
                title=s.title.value,
                authors=[a.name for a in s.authors],
                year=s.year,
                file_ref=s.file_ref,
            )
            for s in sources
        ]
    ), 200


@source_bp.post("")
@login_required
def add_source() -> ResponseReturnValue:
    """Add a source and return its new ID."""
    try:
        body = AddSourceRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    source_id = container.source.add.execute(
        title=body.title,
        authors=body.authors,
        year=body.year,
        file_ref=body.file_ref,
        project_id=body.project_id,
    )

    return jsonify(id=str(source_id.value)), 201


@source_bp.get("/<source_id>")
@login_required
def get_source(source_id: str) -> ResponseReturnValue:
    """Fetch a single source, or respond with not-found."""
    container = current_app.extensions["container"]

    source = container.source.get.execute(source_id=source_id)

    if source is None:
        raise SourceNotFoundError(f"Source '{source_id}' not found")

    return jsonify(
        id=str(source.id.value),
        title=source.title.value,
        authors=[a.name for a in source.authors],
        year=source.year,
        file_ref=source.file_ref,
    ), 200


@source_bp.delete("/<source_id>")
@login_required
def remove_source(source_id: str) -> ResponseReturnValue:
    """Remove a source, or respond with not-found."""
    container = current_app.extensions["container"]

    source = container.source.get.execute(source_id=source_id)

    if source is None:
        raise SourceNotFoundError(f"Source '{source_id}' not found")

    container.source.remove.execute(source_id=source_id)

    return "", 204


@source_bp.patch("/<source_id>/metadata")
@login_required
def update_source_metadata(source_id: str) -> ResponseReturnValue:
    """Replace a source's title, authors and year."""
    try:
        body = UpdateSourceMetadataRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    container = current_app.extensions["container"]

    source = container.source.get.execute(source_id=source_id)

    if source is None:
        raise SourceNotFoundError(f"Source '{source_id}' not found")

    container.source.update_metadata.execute(
        source_id=source_id,
        title=body.title,
        authors=body.authors,
        year=body.year,
    )

    return "", 204


# ---------------------------------------------------------------------------
# Text sources: /api/sources/text (design D2). Every request is scoped to a project
# given as ?projectId=, and the signed-in user must be a member of it (R8).
# ---------------------------------------------------------------------------

MAX_TEXT_BODY_BYTES = 512 * 1024  # D8: 100K chars x <=4 B UTF-8 + metadata
WRITE_LIMIT = "30 per minute"
READ_LIMIT = (
    "120 per minute"  # overrides the app-wide 20/hour default, which would throttle browsing
)
CONTENT_TYPES = ("documentation", "notes", "code", "other")
SORTS = ("updatedAt", "title")

# Domain error code -> request field, so domain-level rejections use the same
# {errors:[{field,message}]} body as request validation.
_DOMAIN_ERROR_FIELDS = {
    "source_library.invalid_source_title": "title",
    "source_library.invalid_text_body": "content",
    "source_library.invalid_description": "description",
    "source_library.invalid_tags": "tags",
    "source_library.invalid_content_type": "contentType",
}


class _FieldErrors(Exception):
    """Carries per-field validation messages out of helpers (HTTP 400)."""

    def __init__(self, errors: list[dict[str, str]]) -> None:
        super().__init__("Invalid request")
        self.errors = errors


def _field_error(field: str, message: str) -> _FieldErrors:
    return _FieldErrors([{"field": field, "message": message}])


@source_bp.errorhandler(_FieldErrors)
def _handle_field_errors(e: _FieldErrors) -> ResponseReturnValue:
    return jsonify(error="Invalid request", errors=e.errors), 400


@source_bp.errorhandler(RateLimitExceeded)
def _handle_rate_limited(e: RateLimitExceeded) -> ResponseReturnValue:
    retry_after = 1
    try:
        window = limiter.current_limit
        if window is not None:
            retry_after = max(1, math.ceil(window.reset_at - time.time()))
    except Exception:  # noqa: BLE001 - header is best-effort
        retry_after = max(1, int(e.limit.limit.get_expiry()))
    response = jsonify(error="Too many requests. Please try again later.")
    response.headers["Retry-After"] = str(retry_after)
    return response, 429


def _project_id() -> UUID:
    """Resolve the request project: 400 if absent or malformed, 404 if not a member."""
    raw = request.args.get("projectId")
    if not raw:
        raise _field_error("projectId", "projectId is required")
    try:
        project_id = UUID(raw)
    except ValueError:
        raise _field_error("projectId", "projectId must be a valid UUID") from None

    container = current_app.extensions["container"]
    project = container.project.get.execute(project_id=str(project_id))
    user_id = str(session["user_id"])
    if project is None or user_id not in {
        str(m.id.value) for m in [project.owner, *project.members]
    }:
        raise SourceNotFoundError(f"Project '{project_id}' not found")
    return project_id


def _load_text(source_id: str, project_id: UUID) -> Source:
    """Return the active text source in the project, else raise not-found (R3, R8)."""
    container = current_app.extensions["container"]
    try:
        source = container.source.get.execute(source_id=source_id)
    except DomainError:  # malformed id
        source = None
    if (
        source is None
        or source.is_removed
        or source.kind != "text"
        or source.project_id != project_id
    ):
        raise SourceNotFoundError(f"Source '{source_id}' not found")
    return source


def _read_text_body() -> TextSourceRequest:
    """Enforce the body cap (D8), then validate the JSON body (R1, R2)."""
    if request.content_length is not None and request.content_length > MAX_TEXT_BODY_BYTES:
        raise _PayloadTooLarge()
    request.max_content_length = MAX_TEXT_BODY_BYTES
    payload = request.get_json(silent=True)
    try:
        return TextSourceRequest.model_validate(payload if isinstance(payload, dict) else {})
    except ValidationError as e:
        errors = []
        for err in e.errors(include_url=False, include_context=False):
            field = str(err["loc"][0]) if err["loc"] else "body"
            errors.append({"field": field, "message": err["msg"].removeprefix("Value error, ")})
        raise _FieldErrors(errors) from None


class _PayloadTooLarge(Exception):
    pass


@source_bp.errorhandler(_PayloadTooLarge)
def _handle_too_large(_: _PayloadTooLarge) -> ResponseReturnValue:
    return jsonify(error="Request body is too large."), 413


def _translate_domain_error(e: DomainError) -> _FieldErrors:
    return _field_error(_DOMAIN_ERROR_FIELDS.get(e.code, "body"), e.message)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _text_dto(source: Source, *, detail: bool) -> dict[str, Any]:
    dto: dict[str, Any] = dict(
        id=str(source.id.value),
        kind=source.kind,
        title=source.title.value,
        description=source.description.value if source.description else None,
        tags=list(source.tags.value),
        contentType=source.content_type.value,
        version=source.version,
        createdAt=_iso(source.created_at),
        updatedAt=_iso(source.updated_at),
    )
    if detail:
        dto["content"] = source.content.value if source.content else ""
    else:
        dto["snippet"] = snippet_of(source)
    return dto


def _page_dto(page: TextSourcePage) -> dict[str, Any]:
    return dict(
        items=[_text_dto(s, detail=False) for s in page.items],
        total=page.total,
        page=page.page,
        pageSize=page.page_size,
    )


def _int_arg(name: str) -> int | None:
    raw = request.args.get(name)
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except ValueError:
        raise _field_error(name, f"{name} must be an integer") from None


def _filter_args() -> tuple[str | None, str | None]:
    """Return (contentType, tag) filters; an unknown contentType is a 400, not 'other'."""
    content_type = request.args.get("contentType") or None
    if content_type is not None and content_type not in CONTENT_TYPES:
        raise _field_error("contentType", f"contentType must be one of: {', '.join(CONTENT_TYPES)}")
    return content_type, (request.args.get("tag") or "").strip() or None


@source_bp.post("/text")
@limiter.limit(WRITE_LIMIT)
@login_required
def create_text_source() -> ResponseReturnValue:
    """Create a text source (R1); 201 with the detail DTO."""
    project_id = _project_id()
    body = _read_text_body()
    container = current_app.extensions["container"]
    try:
        source_id = container.source.add_text.execute(
            title=body.title,
            content=body.content,
            project_id=project_id,
            description=body.description,
            tags=body.tags,
            content_type=body.content_type,
        )
    except DomainError as e:
        raise _translate_domain_error(e) from None
    return jsonify(_text_dto(_load_text(str(source_id.value), project_id), detail=True)), 201


@source_bp.get("/text")
@limiter.limit(READ_LIMIT)
@login_required
def list_text_sources() -> ResponseReturnValue:
    """List text sources with filters, sort and paging (R4)."""
    project_id = _project_id()
    content_type, tag = _filter_args()
    sort = request.args.get("sort") or "updatedAt"
    if sort not in SORTS:
        raise _field_error("sort", f"sort must be one of: {', '.join(SORTS)}")
    container = current_app.extensions["container"]
    page = container.source.list_text.execute(
        project_id=project_id,
        content_type=content_type,
        tag=tag,
        sort=sort,
        page=_int_arg("page"),
        page_size=_int_arg("pageSize"),
    )
    return jsonify(_page_dto(page)), 200


# Registered before /text/<source_id> so "search" is never read as an id.
@source_bp.get("/text/search")
@limiter.limit(READ_LIMIT)
@login_required
def search_text_sources() -> ResponseReturnValue:
    """Search text sources by title, description, tags and content (R7)."""
    project_id = _project_id()
    content_type, tag = _filter_args()
    q = (request.args.get("q") or "").strip()
    if not q:
        raise _field_error("q", "q is required")
    container = current_app.extensions["container"]
    page = container.source.search_text.execute(
        project_id=project_id,
        query=q,
        content_type=content_type,
        tag=tag,
        page=_int_arg("page"),
        page_size=_int_arg("pageSize"),
    )
    return jsonify(_page_dto(page)), 200


@source_bp.get("/text/<source_id>")
@limiter.limit(READ_LIMIT)
@login_required
def get_text_source(source_id: str) -> ResponseReturnValue:
    """Fetch one text source including its content (R3)."""
    project_id = _project_id()
    return jsonify(_text_dto(_load_text(source_id, project_id), detail=True)), 200


@source_bp.put("/text/<source_id>")
@limiter.limit(WRITE_LIMIT)
@login_required
def update_text_source(source_id: str) -> ResponseReturnValue:
    """Replace a text source's editable fields (R5); bumps the version."""
    project_id = _project_id()
    _load_text(source_id, project_id)
    body = _read_text_body()
    container = current_app.extensions["container"]
    try:
        container.source.update_text.execute(
            source_id=source_id,
            title=body.title,
            content=body.content,
            description=body.description,
            tags=body.tags,
            content_type=body.content_type,
            project_id=project_id,
        )
    except SourceNotFound:
        raise SourceNotFoundError(f"Source '{source_id}' not found") from None
    except DomainError as e:
        raise _translate_domain_error(e) from None
    return jsonify(_text_dto(_load_text(source_id, project_id), detail=True)), 200


@source_bp.delete("/text/<source_id>")
@limiter.limit(READ_LIMIT)
@login_required
def delete_text_source(source_id: str) -> ResponseReturnValue:
    """Soft-delete a text source (R6)."""
    project_id = _project_id()
    _load_text(source_id, project_id)
    container = current_app.extensions["container"]
    try:
        container.source.remove.execute(source_id=source_id)
    except SourceNotFound:
        raise SourceNotFoundError(f"Source '{source_id}' not found") from None
    return Response(status=204)
