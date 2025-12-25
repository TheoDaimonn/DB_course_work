from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter()


@router.post(
    "/sessions",
    response_model=schemas.BatchImportResponse,
    summary="Массовый импорт сессий экранного времени",
    description="Принимает список сессий экранного времени и загружает их в базу, записывая ход операции в журнал batch_import_logs.",
)
def batch_import_sessions(payload: schemas.BatchImportRequest, db: Session = Depends(get_db)):
    if not payload.rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No rows provided")

    log = models.BatchImportLog(import_type=payload.import_type, file_name=payload.file_name)
    db.add(log)
    db.flush()  # получить id без коммита

    total_rows = len(payload.rows)
    success_rows = 0
    error_rows = 0
    error_messages: list[str] = []

    try:
        for idx, row in enumerate(payload.rows, start=1):
            try:
                if row.ended_at <= row.started_at:
                    raise ValueError(f"Row {idx}: ended_at must be greater than started_at")
                if row.active_seconds < 0:
                    raise ValueError(f"Row {idx}: active_seconds must be non-negative")

                session = models.ScreenSession(**row.model_dump())
                db.add(session)
                success_rows += 1
            except Exception as e:  # noqa: BLE001
                error_rows += 1
                error_messages.append(str(e))

        log.total_rows = total_rows
        log.success_rows = success_rows
        log.error_rows = error_rows
        log.finished_at = datetime.utcnow()
        if error_rows == 0:
            log.status = "SUCCESS"
        else:
            log.status = "FAILED"
            log.error_message = "\n".join(error_messages)

        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.status = "FAILED"
        log.error_message = f"Fatal error: {e}"
        log.finished_at = datetime.utcnow()
        db.add(log)
        db.commit()

    return schemas.BatchImportResponse(
        id=log.id,
        status=log.status,
        total_rows=log.total_rows,
        success_rows=log.success_rows,
        error_rows=log.error_rows,
        error_message=log.error_message,
    )
