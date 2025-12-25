from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.ApplicationRead],
    summary="Список приложений",
    description="Возвращает постраничный список приложений, по которым учитывается экранное время.",
)
def list_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Application).offset(skip).limit(limit).all()


@router.get(
    "/{application_id}",
    response_model=schemas.ApplicationRead,
    summary="Получить приложение по ID",
    description="Возвращает сведения о приложении по его идентификатору.",
)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(models.Application).get(application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@router.post(
    "/",
    response_model=schemas.ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать приложение",
    description="Создает новое приложение с указанием категории и признака продуктивности.",
)
def create_application(payload: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    application = models.Application(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.put(
    "/{application_id}",
    response_model=schemas.ApplicationRead,
    summary="Обновить приложение",
    description="Изменяет свойства приложения (имя, категория, продуктивность) по идентификатору.",
)
def update_application(application_id: int, payload: schemas.ApplicationBase, db: Session = Depends(get_db)):
    application = db.query(models.Application).get(application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)
    return application


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить приложение",
    description="Удаляет приложение по идентификатору. При наличии ссылок в использовании приложений удаление может быть запрещено.",
)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(models.Application).get(application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    db.delete(application)
    db.commit()
    return None
