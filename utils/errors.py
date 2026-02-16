# dbrecover/utils/errors.py
from dataclasses import dataclass
from typing import Any, Optional, Tuple
from flask import jsonify


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 500
    cause: Optional[Exception] = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def bad_request(
    message: str, code: str = "BAD_REQUEST", cause: Exception | None = None
) -> AppError:
    return AppError(code=code, message=message, status_code=400, cause=cause)


def not_found(
    message: str, code: str = "NOT_FOUND", cause: Exception | None = None
) -> AppError:
    return AppError(code=code, message=message, status_code=404, cause=cause)


def internal_error(
    message: str, code: str = "INTERNAL_ERROR", cause: Exception | None = None
) -> AppError:
    return AppError(code=code, message=message, status_code=500, cause=cause)


def to_http_response(err: AppError):
    payload = {"error": err.message, "code": err.code}

    if err.cause:
        payload["cause"] = str(err.cause)

    return jsonify(payload), err.status_code
