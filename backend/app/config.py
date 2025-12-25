import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://screentime_user:screentime_password@localhost:5432/screentime_db",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
