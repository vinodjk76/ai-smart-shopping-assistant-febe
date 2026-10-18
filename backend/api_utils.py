"""Shared helpers for request validation and consistent JSON errors.

Error format (all endpoints):
    {"error": {"code": "validation_error", "message": "...", "details": {...}}}
"""
from flask import jsonify, request


class ApiError(Exception):
    def __init__(self, message, status=400, code="bad_request", details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details


def error_response(message, status=400, code="bad_request", details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def get_json_body() -> dict:
    if not request.is_json:
        raise ApiError("Request body must be JSON (Content-Type: application/json)",
                       415, "unsupported_media_type")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object", 400, "validation_error")
    return data


def require_int(value, field, minimum=None, maximum=None) -> int:
    if isinstance(value, bool) or value is None:
        raise ApiError(f"'{field}' must be an integer", 400, "validation_error")
    if isinstance(value, float) and not value.is_integer():
        raise ApiError(f"'{field}' must be an integer", 400, "validation_error")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ApiError(f"'{field}' must be an integer", 400, "validation_error")
    if minimum is not None and number < minimum:
        raise ApiError(f"'{field}' must be at least {minimum}", 400, "validation_error")
    if maximum is not None and number > maximum:
        raise ApiError(f"'{field}' must be at most {maximum}", 400, "validation_error")
    return number


def require_text(value, field, max_length, min_length=1) -> str:
    if not isinstance(value, str):
        raise ApiError(f"'{field}' must be a string", 400, "validation_error")
    value = value.strip()
    if len(value) < min_length:
        raise ApiError(f"'{field}' must not be empty", 400, "validation_error")
    if len(value) > max_length:
        raise ApiError(f"'{field}' must be at most {max_length} characters",
                       400, "validation_error")
    return value


def query_float(name, minimum=None, maximum=None):
    raw = request.args.get(name)
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except ValueError:
        raise ApiError(f"Query parameter '{name}' must be a number", 400, "validation_error")
    if minimum is not None and value < minimum:
        raise ApiError(f"Query parameter '{name}' must be at least {minimum}",
                       400, "validation_error")
    if maximum is not None and value > maximum:
        raise ApiError(f"Query parameter '{name}' must be at most {maximum}",
                       400, "validation_error")
    return value


def query_int(name, default, minimum=None, maximum=None):
    raw = request.args.get(name)
    if raw in (None, ""):
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(f"Query parameter '{name}' must be an integer", 400, "validation_error")
    if minimum is not None and value < minimum:
        raise ApiError(f"Query parameter '{name}' must be at least {minimum}",
                       400, "validation_error")
    if maximum is not None and value > maximum:
        raise ApiError(f"Query parameter '{name}' must be at most {maximum}",
                       400, "validation_error")
    return value
