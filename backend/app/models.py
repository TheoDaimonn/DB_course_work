from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()
SCHEMA = "screentime"


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text)

    employees = relationship("Employee", back_populates="department")
    workstations = relationship("Workstation", back_populates="department")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 10", name="chk_position_level"),
        {"schema": SCHEMA},
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    level = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    employees = relationship("Employee", back_populates="position")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    employee = relationship("Employee", back_populates="user", uselist=False)


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    department_id = Column(Integer, ForeignKey(f"{SCHEMA}.departments.id", onupdate="CASCADE", ondelete="SET NULL"))
    position_id = Column(Integer, ForeignKey(f"{SCHEMA}.positions.id", onupdate="CASCADE", ondelete="SET NULL"))
    user_id = Column(Integer, ForeignKey(f"{SCHEMA}.users.id", onupdate="CASCADE", ondelete="SET NULL"), unique=True)
    hired_at = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")
    user = relationship("User", back_populates="employee")
    workstations = relationship("EmployeeWorkstation", back_populates="employee")
    sessions = relationship("ScreenSession", back_populates="employee")


class Workstation(Base):
    __tablename__ = "workstations"
    __table_args__ = (
        UniqueConstraint("hostname", "department_id", name="uq_workstation_host_per_dept"),
        {"schema": SCHEMA},
    )

    id = Column(Integer, primary_key=True)
    hostname = Column(String(100), nullable=False)
    inventory_number = Column(String(50), nullable=False, unique=True)
    department_id = Column(Integer, ForeignKey(f"{SCHEMA}.departments.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    os_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    department = relationship("Department", back_populates="workstations")
    employees = relationship("EmployeeWorkstation", back_populates="workstation")
    sessions = relationship("ScreenSession", back_populates="workstation")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    is_productive = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    session_usages = relationship("SessionApplicationUsage", back_populates="application")


class EmployeeWorkstation(Base):
    __tablename__ = "employee_workstations"
    __table_args__ = (
        PrimaryKeyConstraint("employee_id", "workstation_id"),
        {"schema": SCHEMA},
    )

    employee_id = Column(Integer, ForeignKey(f"{SCHEMA}.employees.id", onupdate="CASCADE", ondelete="CASCADE"))
    workstation_id = Column(Integer, ForeignKey(f"{SCHEMA}.workstations.id", onupdate="CASCADE", ondelete="CASCADE"))
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    unassigned_at = Column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="workstations")
    workstation = relationship("Workstation", back_populates="employees")


class ScreenSession(Base):
    __tablename__ = "screen_sessions"
    __table_args__ = (
        CheckConstraint("ended_at > started_at", name="chk_session_time"),
        {"schema": SCHEMA},
    )

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey(f"{SCHEMA}.employees.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    workstation_id = Column(Integer, ForeignKey(f"{SCHEMA}.workstations.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    active_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    employee = relationship("Employee", back_populates="sessions")
    workstation = relationship("Workstation", back_populates="sessions")
    applications = relationship("SessionApplicationUsage", back_populates="session")


class SessionApplicationUsage(Base):
    __tablename__ = "session_application_usage"
    __table_args__ = (
        PrimaryKeyConstraint("session_id", "application_id"),
        {"schema": SCHEMA},
    )

    session_id = Column(Integer, ForeignKey(f"{SCHEMA}.screen_sessions.id", onupdate="CASCADE", ondelete="CASCADE"))
    application_id = Column(Integer, ForeignKey(f"{SCHEMA}.applications.id", onupdate="CASCADE", ondelete="RESTRICT"))
    active_seconds = Column(Integer, nullable=False)

    session = relationship("ScreenSession", back_populates="applications")
    application = relationship("Application", back_populates="session_usages")


class DailyEmployeeStat(Base):
    __tablename__ = "daily_employee_stats"
    __table_args__ = (
        PrimaryKeyConstraint("employee_id", "stat_date"),
        CheckConstraint("total_seconds >= 0", name="chk_daily_total_seconds"),
        {"schema": SCHEMA},
    )

    employee_id = Column(Integer, ForeignKey(f"{SCHEMA}.employees.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    stat_date = Column(Date, nullable=False)
    total_seconds = Column(Integer, nullable=False, default=0)
    sessions_count = Column(Integer, nullable=False, default=0)
    avg_session_seconds = Column(Numeric(10, 2), nullable=False, default=0)


class BatchImportLog(Base):
    __tablename__ = "batch_import_logs"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    import_type = Column(String(50), nullable=False)
    file_name = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime)
    total_rows = Column(Integer, default=0, nullable=False)
    success_rows = Column(Integer, default=0, nullable=False)
    error_rows = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="IN_PROGRESS", nullable=False)
    error_message = Column(Text)
