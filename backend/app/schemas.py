from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Базовые сущности


class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentRead(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


class PositionBase(BaseModel):
    name: str
    level: int = Field(ge=1, le=10)
    description: Optional[str] = None
    is_active: bool = True


class PositionCreate(PositionBase):
    pass


class PositionRead(PositionBase):
    id: int

    class Config:
        from_attributes = True


class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    hired_at: date
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    hired_at: Optional[date] = None
    is_active: Optional[bool] = None


class EmployeeRead(EmployeeBase):
    id: int

    class Config:
        from_attributes = True


class WorkstationBase(BaseModel):
    hostname: str
    inventory_number: str
    department_id: int
    os_name: str
    is_active: bool = True


class WorkstationCreate(WorkstationBase):
    pass


class WorkstationRead(WorkstationBase):
    id: int

    class Config:
        from_attributes = True


class ApplicationBase(BaseModel):
    name: str
    code: str
    category: str
    is_productive: bool
    is_active: bool = True


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: int

    class Config:
        from_attributes = True


# ===== Сессии экранного времени =====


class ScreenSessionBase(BaseModel):
    employee_id: int
    workstation_id: int
    started_at: datetime
    ended_at: datetime
    active_seconds: int


class ScreenSessionCreate(ScreenSessionBase):
    pass


class ScreenSessionRead(ScreenSessionBase):
    id: int

    class Config:
        from_attributes = True


#  Отчеты 


class EmployeeDailyStatRead(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    department_name: Optional[str]
    position_name: Optional[str]
    stat_date: date
    total_seconds: int
    sessions_count: int
    avg_session_seconds: float


class DepartmentDailyStatRead(BaseModel):
    department_id: int
    department_name: str
    stat_date: date
    total_seconds: int
    sessions_count: int


class EmployeeLastActivityRead(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    workstation_id: int
    hostname: str
    started_at: datetime
    ended_at: datetime
    active_seconds: int


class TopOverworkedEmployeeRead(BaseModel):
    employee_id: int
    avg_hours_per_day: float
    total_days: int


class DepartmentLoadRead(BaseModel):
    department_id: int
    total_seconds: int
    avg_seconds_per_employee: float


# Batch import


class BatchSessionRow(BaseModel):
    employee_id: int
    workstation_id: int
    started_at: datetime
    ended_at: datetime
    active_seconds: int


class BatchImportRequest(BaseModel):
    import_type: str = "sessions"
    file_name: Optional[str] = None
    rows: List[BatchSessionRow]


class BatchImportResponse(BaseModel):
    id: int
    status: str
    total_rows: int
    success_rows: int
    error_rows: int
    error_message: Optional[str] = None
