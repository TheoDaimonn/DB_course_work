from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.ScreenSessionRead],
    summary="Список сессий экранного времени",
    description="Возвращает постраничный список сессий экранного времени, отсортированных по дате начала (от новых к старым).",
)
def list_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.ScreenSession).order_by(models.ScreenSession.started_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{session_id}",
    response_model=schemas.ScreenSessionRead,
    summary="Получить сессию по ID",
    description="Возвращает данные о конкретной сессии экранного времени по ее идентификатору.",
)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.ScreenSession).get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.post(
    "/",
    response_model=schemas.ScreenSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать сессию экранного времени",
    description="Создает новую запись о сессии экранного времени сотрудника за конкретной рабочей станцией.",
)
def create_session(payload: schemas.ScreenSessionCreate, db: Session = Depends(get_db)):
    if payload.ended_at <= payload.started_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ended_at must be greater than started_at")
    if payload.active_seconds < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="active_seconds must be non-negative")

    session = models.ScreenSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить сессию экранного времени",
    description="Удаляет сессию экранного времени по идентификатору. Триггеры пересчитывают агрегированную статистику.",
)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.ScreenSession).get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
    return None
