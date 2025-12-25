from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..utils import sql as sql_utils

router = APIRouter()


@router.get(
    "/employee-daily",
    response_model=List[schemas.EmployeeDailyStatRead],
    summary="Суточная статистика по сотруднику",
    description="Возвращает агрегированную статистику по сотруднику за указанный день (общее время, число сессий, средняя длительность).",
)
def employee_daily(employee_id: int, stat_date: date, db: Session = Depends(get_db)):
    rows = sql_utils.fetch_all(
        db,
        "SELECT * FROM screentime.v_employee_daily_stats WHERE employee_id = :employee_id AND stat_date = :stat_date",
        {"employee_id": employee_id, "stat_date": stat_date},
    )
    return rows


@router.get(
    "/department-daily",
    response_model=List[schemas.DepartmentDailyStatRead],
    summary="Суточная статистика по отделам",
    description="Возвращает суммарное экранное время и количество сессий по каждому отделу за выбранную дату.",
)
def department_daily(stat_date: date, db: Session = Depends(get_db)):
    rows = sql_utils.fetch_all(
        db,
        "SELECT * FROM screentime.v_department_daily_stats WHERE stat_date = :stat_date",
        {"stat_date": stat_date},
    )
    return rows


@router.get(
    "/last-activity",
    response_model=List[schemas.EmployeeLastActivityRead],
    summary="Последняя активность сотрудников",
    description="Возвращает последнюю зафиксированную сессию экранного времени для каждого сотрудника.",
)
def last_activity(db: Session = Depends(get_db)):
    rows = sql_utils.fetch_all(db, "SELECT * FROM screentime.v_employee_last_activity")
    return rows


@router.get(
    "/top-overworked",
    response_model=List[schemas.TopOverworkedEmployeeRead],
    summary="Список перегруженных сотрудников",
    description="Возвращает сотрудников, у которых среднесуточное экранное время за период превышает заданный порог (min_hours_per_day).",
)
def top_overworked(date_from: date, date_to: date, min_hours_per_day: float = 8.0, db: Session = Depends(get_db)):
    rows = sql_utils.fetch_all(
        db,
        "SELECT * FROM screentime.fn_top_overworked_employees(:date_from, :date_to, :min_hours_per_day)",
        {"date_from": date_from, "date_to": date_to, "min_hours_per_day": min_hours_per_day},
    )
    return rows


@router.get(
    "/department-load",
    response_model=List[schemas.DepartmentLoadRead],
    summary="Нагрузка по отделам за период",
    description="Возвращает суммарное и среднее экранное время по каждому отделу за указанный период.",
)
def department_load(date_from: date, date_to: date, db: Session = Depends(get_db)):
    rows = sql_utils.fetch_all(
        db,
        "SELECT * FROM screentime.fn_department_load(:date_from, :date_to)",
        {"date_from": date_from, "date_to": date_to},
    )
    return rows
