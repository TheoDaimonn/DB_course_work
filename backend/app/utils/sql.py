from typing import Any, Iterable, List, Mapping

from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session


def fetch_all(db: Session, sql: str, params: Mapping[str, Any] | None = None) -> List[Mapping[str, Any]]:
    result: Result = db.execute(text(sql), params or {})
    rows = result.mappings().all()
    return [dict(row) for row in rows]
