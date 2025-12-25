from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.EmployeeRead],
    summary="Список сотрудников",
    description="Возвращает постраничный список сотрудников с возможностью задать смещение (skip) и лимит (limit).",
)
def list_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Employee).offset(skip).limit(limit).all()


@router.get(
    "/{employee_id}",
    response_model=schemas.EmployeeRead,
    summary="Получить сотрудника по ID",
    description="Возвращает подробную информацию о сотруднике по его идентификатору.",
)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post(
    "/",
    response_model=schemas.EmployeeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать нового сотрудника",
    description="Создает запись о сотруднике на основе переданных данных (ФИО, отдел, должность, дата найма и т.д.).",
)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    employee = models.Employee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.put(
    "/{employee_id}",
    response_model=schemas.EmployeeRead,
    summary="Обновить данные сотрудника",
    description="Изменяет данные сотрудника по идентификатору. Можно передавать только изменяемые поля.",
)
def update_employee(employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    return employee


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить сотрудника",
    description="Удаляет сотрудника по идентификатору. При удалении срабатывают каскадные ограничения в связанных таблицах.",
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).get(employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    db.delete(employee)
    db.commit()
    return None
