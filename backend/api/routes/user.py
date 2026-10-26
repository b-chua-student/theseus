from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from api.extensions import limiter
from api.schemas.user_requests import CreateUserRequest, UpdateUserRequest
from api.schemas.user_responses import UserResponseDTO
from services.user.create_user import CreateUserService
from services.user.delete_user import DeleteUserService
from services.user.get_user import GetUserService
from services.user.update_user import UpdateUserService

users_bp = Blueprint("users", __name__)


@users_bp.post("")
@limiter.limit("5/minute")
def create_user() -> ResponseReturnValue:
    """Validate the request and create a user.

    Returns:
        201 with the serialized user, or 400 on invalid input.
    """
    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = CreateUserRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    service: CreateUserService = current_app.extensions["create_user_service"]

    try:
        user = service.execute(email=payload.email, display_name=payload.display_name)
    except ValueError as err:
        return jsonify({"error": str(err)}), 409

    return jsonify(UserResponseDTO.from_domain(user).to_dict()), 201


@users_bp.get("/<user_id>")
def get_user(user_id: str) -> ResponseReturnValue:
    """Retrieve a single user by its UUID.

    Args:
        user_id: String representation of the user UUID from the URL path.

    Returns:
        200 with the serialized user, 400 on invalid UUID, or 404 if not found.
    """
    try:
        parsed_id = UUID(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user ID format."}), 400

    service: GetUserService = current_app.extensions["get_user_service"]

    try:
        user = service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify(UserResponseDTO.from_domain(user).to_dict()), 200


@users_bp.patch("/<user_id>")
@limiter.limit("10/hour")
def update_user(user_id: str) -> ResponseReturnValue:
    """Update an existing user's display name and/or email by its UUID.

    Args:
        user_id: String representation of the user UUID from the URL path.

    Returns:
        200 with the serialized updated user, 400 on invalid UUID or JSON
        payload, 404 if the user does not exist, or 409 if the email is taken.
    """
    try:
        parsed_id = UUID(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user ID format."}), 400

    raw_body = request.get_json(silent=True)
    if not isinstance(raw_body, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    try:
        payload = UpdateUserRequest.model_validate(raw_body)
    except ValidationError as err:
        return jsonify({"error": err.errors()}), 400

    if payload.display_name is None and payload.email is None:
        return jsonify(
            {"error": "At least one of 'display_name' or 'email' must be provided."}
        ), 400

    service: UpdateUserService = current_app.extensions["update_user_service"]

    try:
        user = service.execute(
            parsed_id,
            display_name=payload.display_name,
            email=payload.email,
        )
    except ValueError as err:
        error_msg = str(err)
        status = 409 if "already exists" in error_msg else 404
        return jsonify({"error": error_msg}), status

    return jsonify(UserResponseDTO.from_domain(user).to_dict()), 200


@users_bp.delete("/<user_id>")
@limiter.limit("10/hour")
def delete_user(user_id: str) -> ResponseReturnValue:
    """Delete a user by its UUID.

    Args:
        user_id: String representation of the user UUID from the URL path.

    Returns:
        204 No Content on success, 400 if the UUID is invalid, or 404 if not found.
    """
    try:
        parsed_id = UUID(user_id)
    except ValueError:
        return jsonify({"error": "Invalid user ID format."}), 400

    service: DeleteUserService = current_app.extensions["delete_user_service"]

    try:
        service.execute(parsed_id)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return "", 204
