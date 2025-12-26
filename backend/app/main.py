from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .routers import employees, departments, workstations, applications, sessions, reports, batch_import
from .api_errors import (
    handle_http_exception,
    handle_integrity_error,
    handle_sqlalchemy_error,
    handle_unexpected_error,
    handle_validation_error,
)

app = FastAPI(
    title="Screen Time Tracking API",
    description="API для учета экранного времени сотрудников (курсовой проект)",
    version="1.0.0",
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return handle_http_exception(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return handle_validation_error(request, exc)


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    return handle_integrity_error(request, exc)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return handle_sqlalchemy_error(request, exc)


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):  # noqa: BLE001
    return handle_unexpected_error(request, exc)


app.include_router(departments.router, prefix="/api/departments", tags=["Departments"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(workstations.router, prefix="/api/workstations", tags=["Workstations"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(batch_import.router, prefix="/api/batch-import", tags=["BatchImport"])
