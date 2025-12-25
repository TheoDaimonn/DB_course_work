from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.WorkstationRead],
    summary="Список рабочих станций",
    description="Возвращает постраничный список рабочих станций (ПК/ноутбуков).",
)
def list_workstations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Workstation).offset(skip).limit(limit).all()


@router.get(
    "/{workstation_id}",
    response_model=schemas.WorkstationRead,
    summary="Получить рабочую станцию по ID",
    description="Возвращает данные о рабочей станции (hostname, инвентарный номер, отдел, ОС) по идентификатору.",
)
def get_workstation(workstation_id: int, db: Session = Depends(get_db)):
    workstation = db.query(models.Workstation).get(workstation_id)
    if not workstation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation not found")
    return workstation


@router.post(
    "/",
    response_model=schemas.WorkstationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать рабочую станцию",
    description="Создает новую рабочую станцию и привязывает ее к подразделению.",
)
def create_workstation(payload: schemas.WorkstationCreate, db: Session = Depends(get_db)):
    workstation = models.Workstation(**payload.model_dump())
    db.add(workstation)
    db.commit()
    db.refresh(workstation)
    return workstation


@router.put(
    "/{workstation_id}",
    response_model=schemas.WorkstationRead,
    summary="Обновить рабочую станцию",
    description="Изменяет данные рабочей станции по идентификатору.",
)
def update_workstation(workstation_id: int, payload: schemas.WorkstationBase, db: Session = Depends(get_db)):
    workstation = db.query(models.Workstation).get(workstation_id)
    if not workstation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(workstation, field, value)

    db.commit()
    db.refresh(workstation)
    return workstation


@router.delete(
    "/{workstation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить рабочую станцию",
    description="Удаляет рабочую станцию по идентификатору. При удалении каскадно удаляются связанные сессии.",
)
def delete_workstation(workstation_id: int, db: Session = Depends(get_db)):
    workstation = db.query(models.Workstation).get(workstation_id)
    if not workstation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workstation not found")
    db.delete(workstation)
    db.commit()
    return None
