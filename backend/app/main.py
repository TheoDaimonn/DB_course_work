from fastapi import FastAPI

from .routers import employees, departments, workstations, applications, sessions, reports, batch_import

app = FastAPI(
    title="Screen Time Tracking API",
    description="API для учета экранного времени сотрудников (курсовой проект)",
    version="1.0.0",
)

app.include_router(departments.router, prefix="/api/departments", tags=["Departments"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(workstations.router, prefix="/api/workstations", tags=["Workstations"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(batch_import.router, prefix="/api/batch-import", tags=["BatchImport"])
