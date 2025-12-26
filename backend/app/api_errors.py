from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def _request_id(request: Request) -> Optional[str]:
    return getattr(getattr(request, "state", None), "request_id", None)


def error_payload(*, code: str, message: str, request_id: Optional[str] = None, details: Any = None) -> dict:
    err: dict[str, Any] = {"code": code, "message": message}
    if request_id:
        err["request_id"] = request_id
    if details is not None:
        err["details"] = details
    return {"ok": False, "error": err}


def http_error_code(status_code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
    }.get(status_code, "HTTP_ERROR")


def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    rid = _request_id(request)

    if isinstance(exc.detail, dict):
        # Если detail уже в "нашем" формате — просто дополним request_id при необходимости.
        if exc.detail.get("ok") is False and isinstance(exc.detail.get("error"), dict):
            payload = exc.detail
            if rid and "request_id" not in payload["error"]:
                payload["error"]["request_id"] = rid
            return JSONResponse(status_code=exc.status_code, content=payload)

        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(code=http_error_code(exc.status_code), message="Ошибка запроса", request_id=rid, details=exc.detail),
        )

    message = str(exc.detail) if exc.detail else "Ошибка запроса"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code=http_error_code(exc.status_code), message=message, request_id=rid),
    )


def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    rid = _request_id(request)
    details = []
    for e in exc.errors():
        # e: {type, loc, msg, input, ctx}
        details.append(
            {
                "loc": list(e.get("loc", [])),
                "message": e.get("msg"),
                "type": e.get("type"),
            }
        )
    return JSONResponse(
        status_code=422,
        content=error_payload(code="VALIDATION_ERROR", message="Некорректные параметры запроса", request_id=rid, details=details),
    )


def _extract_constraint_name(exc: IntegrityError) -> Optional[str]:
    orig = getattr(exc, "orig", None)
    diag = getattr(orig, "diag", None)
    return getattr(diag, "constraint_name", None) if diag else None


def _extract_pgcode(exc: IntegrityError | SQLAlchemyError) -> Optional[str]:
    orig = getattr(exc, "orig", None)
    return getattr(orig, "pgcode", None)


def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    rid = _request_id(request)
    pgcode = _extract_pgcode(exc)
    constraint = _extract_constraint_name(exc)
# PostgreSQL error codes: https://www.postgresql.org/docs/current/errcodes-appendix.html
    if pgcode == "23505":  # unique_violation
        status_code = 409
        code = "UNIQUE_VIOLATION"
        message = "Запись с такими уникальными значениями уже существует"
    elif pgcode == "23503":  # foreign_key_violation
        status_code = 409
        code = "FOREIGN_KEY_VIOLATION"
        message = "Невозможно выполнить операцию: есть зависимые или отсутствующие связанные данные"
    elif pgcode == "23514":  # check_violation
        status_code = 400
        code = "CHECK_VIOLATION"
        message = "Нарушено ограничение данных"
    elif pgcode == "23502":  # not_null_violation
        status_code = 400
        code = "NOT_NULL_VIOLATION"
        message = "Не заполнены обязательные поля"
    else:
        status_code = 409
        code = "INTEGRITY_ERROR"
        message = "Ошибка целостности данных"

    details: dict[str, Any] = {}
    if pgcode:
        details["pgcode"] = pgcode
    if constraint:
        details["constraint"] = constraint

    return JSONResponse(
        status_code=status_code,
        content=error_payload(code=code, message=message, request_id=rid, details=details or None),
    )


def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    rid = _request_id(request)
    details: dict[str, Any] = {}
    pgcode = _extract_pgcode(exc)
    if pgcode:
        details["pgcode"] = pgcode
    details["type"] = exc.__class__.__name__

    return JSONResponse(
        status_code=500,
        content=error_payload(code="DB_ERROR", message="Ошибка базы данных", request_id=rid, details=details or None),
    )


def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    rid = _request_id(request)
    return JSONResponse(
        status_code=500,
        content=error_payload(code="INTERNAL_ERROR", message="Внутренняя ошибка сервера", request_id=rid),
    )



