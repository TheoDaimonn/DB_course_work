from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.DepartmentRead],
    summary="Список отделов",
    description="Возвращает постраничный список подразделений компании.",
)
def list_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Department).offset(skip).limit(limit).all()


@router.get(
    "/{department_id}",
    response_model=schemas.DepartmentRead,
    summary="Получить отдел по ID",
    description="Возвращает сведения о подразделении по его идентификатору.",
)
def get_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(models.Department).get(department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


@router.post(
    "/",
    response_model=schemas.DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать отдел",
    description="Создает новое подразделение компании (название, код, описание).",
)
def create_department(payload: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    department = models.Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.put(
    "/{department_id}",
    response_model=schemas.DepartmentRead,
    summary="Обновить отдел",
    description="Изменяет данные подразделения по идентификатору.",
)
def update_department(department_id: int, payload: schemas.DepartmentBase, db: Session = Depends(get_db)):
    department = db.query(models.Department).get(department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)
    return department


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить отдел",
    description="Удаляет подразделение по идентификатору. При удалении могут каскадно удаляться связанные сущности.",
)
def delete_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(models.Department).get(department_id)
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    db.delete(department)
    db.commit()
    return None
