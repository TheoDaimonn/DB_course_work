"""Скрипт генерации тестовых данных 

    python -m app.scripts.generate_test_data
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from ..db import SessionLocal
from .. import models


FIRST_NAMES = [
    "Иван",
    "Петр",
    "Сергей",
    "Андрей",
    "Дмитрий",
    "Ольга",
    "Анна",
    "Екатерина",
    "Мария",
    "Елена",
]

LAST_NAMES = [
    "Иванов",
    "Петров",
    "Сидоров",
    "Смирнов",
    "Кузнецов",
    "Попова",
    "Козлова",
    "Новикова",
    "Федорова",
    "Васильева",
]

DEPARTMENTS = [
    ("Отдел разработки", "DEV"),
    ("Отдел тестирования", "QA"),
    ("Отдел аналитики", "BA"),
    ("Отдел поддержки", "SUP"),
]

POSITIONS = [
    ("Junior Developer", 2),
    ("Middle Developer", 5),
    ("Senior Developer", 8),
    ("QA Engineer", 4),
    ("Business Analyst", 5),
]

APPLICATIONS = [
    ("Visual Studio Code", "vscode", "development", True),
    ("Google Chrome", "chrome", "browser", False),
    ("Postman", "postman", "tools", True),
    ("Slack", "slack", "communication", True),
    ("YouTube", "youtube", "entertainment", False),
]


def create_basic_data(db: Session):
    # Departments
    if not db.query(models.Department).count():
        for name, code in DEPARTMENTS:
            db.add(models.Department(name=name, code=code))

    # Positions
    if not db.query(models.Position).count():
        for name, level in POSITIONS:
            db.add(models.Position(name=name, level=level))

    # Applications
    if not db.query(models.Application).count():
        for name, code, category, productive in APPLICATIONS:
            db.add(
                models.Application(
                    name=name,
                    code=code,
                    category=category,
                    is_productive=productive,
                )
            )

    db.commit()


def create_employees_and_workstations(db: Session, employees_count: int = 500, workstations_count: int = 500):
    departments = db.query(models.Department).all()
    positions = db.query(models.Position).all()

    # Employees
    if not db.query(models.Employee).count():
        for i in range(employees_count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = f"user{i}@example.com"
            department = random.choice(departments)
            position = random.choice(positions)
            hired_at = date.today() - timedelta(days=random.randint(30, 365))

            db.add(
                models.Employee(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    department_id=department.id,
                    position_id=position.id,
                    hired_at=hired_at,
                )
            )

    db.commit()

    # Workstations
    if not db.query(models.Workstation).count():
        for i in range(workstations_count):
            department = random.choice(departments)
            hostname = f"pc-{department.code.lower()}-{i:03d}"
            inventory_number = f"INV-{department.code}-{i:04d}"
            os_name = random.choice(["Windows 10", "Windows 11", "Ubuntu 22.04"])

            db.add(
                models.Workstation(
                    hostname=hostname,
                    inventory_number=inventory_number,
                    department_id=department.id,
                    os_name=os_name,
                )
            )

    db.commit()


def create_screen_sessions(db: Session, days: int = 30, sessions_per_employee_per_day: int = 3):
    employees = db.query(models.Employee).all()
    workstations = db.query(models.Workstation).all()

    if not employees or not workstations:
        return

    start_date = date.today() - timedelta(days=days)

    for emp in employees:
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            workstation = random.choice(workstations)

            for _ in range(sessions_per_employee_per_day):
                start_hour = random.randint(8, 18)
                duration_minutes = random.randint(15, 120)
                started_at = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=start_hour)
                ended_at = started_at + timedelta(minutes=duration_minutes)
                active_seconds = duration_minutes * 60

                db.add(
                    models.ScreenSession(
                        employee_id=emp.id,
                        workstation_id=workstation.id,
                        started_at=started_at,
                        ended_at=ended_at,
                        active_seconds=active_seconds,
                    )
                )

    db.commit()


def main():
    db = SessionLocal()
    try:
        create_basic_data(db)
        create_employees_and_workstations(db)
        create_screen_sessions(db, days=30, sessions_per_employee_per_day=3)
    finally:
        db.close()


if __name__ == "__main__":
    main()
