-- Инициализация схемы БД для системы учета экранного времени сотрудников
CREATE SCHEMA IF NOT EXISTS screentime;
SET search_path TO screentime, public;

-- Таблицы справочников и сущностей

CREATE TABLE departments (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    code            VARCHAR(20) NOT NULL UNIQUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    description     TEXT
);

CREATE TABLE positions (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    level           INTEGER NOT NULL CHECK (level BETWEEN 1 AND 10),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('admin','manager','viewer')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE employees (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    email           VARCHAR(100) UNIQUE,
    department_id   INTEGER REFERENCES departments(id)
                        ON UPDATE CASCADE ON DELETE SET NULL,
    position_id     INTEGER REFERENCES positions(id)
                        ON UPDATE CASCADE ON DELETE SET NULL,
    user_id         INTEGER UNIQUE REFERENCES users(id)
                        ON UPDATE CASCADE ON DELETE SET NULL,
    hired_at        DATE NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE workstations (
    id                  SERIAL PRIMARY KEY,
    hostname            VARCHAR(100) NOT NULL,
    inventory_number    VARCHAR(50) NOT NULL UNIQUE,
    department_id       INTEGER NOT NULL REFERENCES departments(id)
                            ON UPDATE CASCADE ON DELETE CASCADE,
    os_name             VARCHAR(50) NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_workstation_host_per_dept UNIQUE (hostname, department_id)
);

CREATE TABLE applications (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    code            VARCHAR(50) NOT NULL UNIQUE,
    category        VARCHAR(50) NOT NULL,
    is_productive   BOOLEAN NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- Связь N:M сотрудников и рабочих станций
CREATE TABLE employee_workstations (
    employee_id     INTEGER NOT NULL REFERENCES employees(id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
    workstation_id  INTEGER NOT NULL REFERENCES workstations(id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
    assigned_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    unassigned_at   TIMESTAMP,
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
    note            TEXT,
    PRIMARY KEY (employee_id, workstation_id)
);

-- Транзакционная таблица экранных сессий
CREATE TABLE screen_sessions (
    id              BIGSERIAL PRIMARY KEY,
    employee_id     INTEGER NOT NULL REFERENCES employees(id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
    workstation_id  INTEGER NOT NULL REFERENCES workstations(id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
    started_at      TIMESTAMP NOT NULL,
    ended_at        TIMESTAMP NOT NULL,
    active_seconds  INTEGER NOT NULL CHECK (active_seconds >= 0),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_session_time CHECK (ended_at > started_at)
);

-- Использование приложений в рамках сессии (N:M через детальную таблицу)
CREATE TABLE session_application_usage (
    session_id      BIGINT NOT NULL REFERENCES screen_sessions(id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
    application_id  INTEGER NOT NULL REFERENCES applications(id)
                        ON UPDATE CASCADE ON DELETE RESTRICT,
    active_seconds  INTEGER NOT NULL CHECK (active_seconds >= 0),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    note            TEXT,
    PRIMARY KEY (session_id, application_id)
);

-- Агрегированные суточные статистики по сотруднику
CREATE TABLE daily_employee_stats (
    employee_id         INTEGER NOT NULL REFERENCES employees(id)
                            ON UPDATE CASCADE ON DELETE CASCADE,
    stat_date           DATE    NOT NULL,
    total_seconds       INTEGER NOT NULL DEFAULT 0 CHECK (total_seconds >= 0),
    sessions_count      INTEGER NOT NULL DEFAULT 0 CHECK (sessions_count >= 0),
    avg_session_seconds NUMERIC(10,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (employee_id, stat_date)
);

-- Журнал аудита изменений
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    table_name      TEXT NOT NULL,
    operation       VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE')),
    record_id       TEXT NOT NULL,
    changed_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    changed_by      TEXT,
    old_values      JSONB,
    new_values      JSONB
);

-- Лог batch-импорта
CREATE TABLE batch_import_logs (
    id              BIGSERIAL PRIMARY KEY,
    import_type     VARCHAR(50) NOT NULL,
    file_name       TEXT,
    started_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMP,
    total_rows      INTEGER NOT NULL DEFAULT 0,
    success_rows    INTEGER NOT NULL DEFAULT 0,
    error_rows      INTEGER NOT NULL DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS'
                        CHECK (status IN ('IN_PROGRESS','SUCCESS','FAILED')),
    error_message   TEXT
);

-- Индексы

CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_screen_sessions_employee_date ON screen_sessions(employee_id, started_at);
CREATE INDEX idx_screen_sessions_workstation ON screen_sessions(workstation_id);
CREATE INDEX idx_daily_stats_employee_date ON daily_employee_stats(employee_id, stat_date);
CREATE INDEX idx_audit_log_table_changed_at ON audit_log(table_name, changed_at);
CREATE INDEX idx_applications_code ON applications(code);

-- Функции и триггеры аудита

CREATE OR REPLACE FUNCTION trg_write_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    v_record_id TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_record_id := NEW.id::TEXT;
        INSERT INTO screentime.audit_log(table_name, operation, record_id, old_values, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, v_record_id, NULL, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := NEW.id::TEXT;
        INSERT INTO screentime.audit_log(table_name, operation, record_id, old_values, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, v_record_id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        v_record_id := OLD.id::TEXT;
        INSERT INTO screentime.audit_log(table_name, operation, record_id, old_values, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, v_record_id, to_jsonb(OLD), NULL);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_employees
AFTER INSERT OR UPDATE OR DELETE ON employees
FOR EACH ROW EXECUTE FUNCTION trg_write_audit_log();

CREATE TRIGGER trg_audit_workstations
AFTER INSERT OR UPDATE OR DELETE ON workstations
FOR EACH ROW EXECUTE FUNCTION trg_write_audit_log();

CREATE TRIGGER trg_audit_screen_sessions
AFTER INSERT OR UPDATE OR DELETE ON screen_sessions
FOR EACH ROW EXECUTE FUNCTION trg_write_audit_log();

CREATE TRIGGER trg_audit_applications
AFTER INSERT OR UPDATE OR DELETE ON applications
FOR EACH ROW EXECUTE FUNCTION trg_write_audit_log();

-- Функции и триггеры для агрегатов daily_employee_stats

CREATE OR REPLACE FUNCTION fn_recalculate_daily_employee_stat(p_employee_id INT, p_date DATE)
RETURNS VOID AS $$
DECLARE
    v_total_seconds   INTEGER;
    v_sessions_count  INTEGER;
    v_avg_seconds     NUMERIC(10,2);
BEGIN
    SELECT
        COALESCE(SUM(active_seconds), 0),
        COUNT(*),
        COALESCE(AVG(active_seconds), 0)
    INTO v_total_seconds, v_sessions_count, v_avg_seconds
    FROM screen_sessions
    WHERE employee_id = p_employee_id
      AND started_at::DATE = p_date;

    IF v_sessions_count = 0 THEN
        DELETE FROM daily_employee_stats
        WHERE employee_id = p_employee_id AND stat_date = p_date;
    ELSE
        INSERT INTO daily_employee_stats(employee_id, stat_date, total_seconds, sessions_count, avg_session_seconds)
        VALUES (p_employee_id, p_date, v_total_seconds, v_sessions_count, v_avg_seconds)
        ON CONFLICT (employee_id, stat_date) DO UPDATE
        SET total_seconds = EXCLUDED.total_seconds,
            sessions_count = EXCLUDED.sessions_count,
            avg_session_seconds = EXCLUDED.avg_session_seconds;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trg_update_daily_stats()
RETURNS TRIGGER AS $$
DECLARE
    v_emp_id INT;
    v_date_old DATE;
    v_date_new DATE;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_emp_id := NEW.employee_id;
        v_date_new := NEW.started_at::DATE;
        PERFORM screentime.fn_recalculate_daily_employee_stat(v_emp_id, v_date_new);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        v_emp_id := NEW.employee_id;
        v_date_new := NEW.started_at::DATE;
        v_date_old := OLD.started_at::DATE;
        IF v_emp_id = OLD.employee_id AND v_date_new = v_date_old THEN
            PERFORM screentime.fn_recalculate_daily_employee_stat(v_emp_id, v_date_new);
        ELSE
            PERFORM screentime.fn_recalculate_daily_employee_stat(OLD.employee_id, v_date_old);
            PERFORM screentime.fn_recalculate_daily_employee_stat(v_emp_id, v_date_new);
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        v_emp_id := OLD.employee_id;
        v_date_old := OLD.started_at::DATE;
        PERFORM screentime.fn_recalculate_daily_employee_stat(v_emp_id, v_date_old);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_screen_sessions_daily_stats
AFTER INSERT OR UPDATE OR DELETE ON screen_sessions
FOR EACH ROW EXECUTE FUNCTION trg_update_daily_stats();

-- Скалярная и табличные функции для отчетов

CREATE OR REPLACE FUNCTION fn_employee_daily_load(p_employee_id INT, p_date DATE)
RETURNS NUMERIC(10,2) AS $$
DECLARE
    v_total_seconds INTEGER;
BEGIN
    SELECT COALESCE(SUM(active_seconds), 0)
    INTO v_total_seconds
    FROM screen_sessions
    WHERE employee_id = p_employee_id
      AND started_at::DATE = p_date;

    RETURN v_total_seconds / 3600.0;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION fn_top_overworked_employees(
    p_date_from DATE,
    p_date_to   DATE,
    p_min_hours_per_day NUMERIC
)
RETURNS TABLE (
    employee_id      INT,
    avg_hours_per_day NUMERIC(10,2),
    total_days       INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        des.employee_id,
        (SUM(des.total_seconds) / 3600.0) / COUNT(DISTINCT des.stat_date) AS avg_hours_per_day,
        COUNT(DISTINCT des.stat_date) AS total_days
    FROM daily_employee_stats des
    WHERE des.stat_date BETWEEN p_date_from AND p_date_to
    GROUP BY des.employee_id
    HAVING (SUM(des.total_seconds) / 3600.0) / COUNT(DISTINCT des.stat_date) >= p_min_hours_per_day
    ORDER BY avg_hours_per_day DESC;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION fn_department_load(
    p_date_from DATE,
    p_date_to   DATE
)
RETURNS TABLE (
    department_id    INT,
    total_seconds    BIGINT,
    avg_seconds_per_employee NUMERIC(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.department_id,
        SUM(des.total_seconds) AS total_seconds,
        AVG(des.total_seconds)::NUMERIC(10,2) AS avg_seconds_per_employee
    FROM daily_employee_stats des
    JOIN employees e ON e.id = des.employee_id
    WHERE des.stat_date BETWEEN p_date_from AND p_date_to
    GROUP BY e.department_id
    ORDER BY total_seconds DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Представления

CREATE OR REPLACE VIEW v_employee_daily_stats AS
SELECT
    des.employee_id,
    e.first_name,
    e.last_name,
    d.name AS department_name,
    p.name AS position_name,
    des.stat_date,
    des.total_seconds,
    des.sessions_count,
    des.avg_session_seconds
FROM daily_employee_stats des
JOIN employees e ON e.id = des.employee_id
LEFT JOIN departments d ON d.id = e.department_id
LEFT JOIN positions p ON p.id = e.position_id;

CREATE OR REPLACE VIEW v_department_daily_stats AS
SELECT
    d.id AS department_id,
    d.name AS department_name,
    des.stat_date,
    SUM(des.total_seconds) AS total_seconds,
    SUM(des.sessions_count) AS sessions_count
FROM daily_employee_stats des
JOIN employees e ON e.id = des.employee_id
JOIN departments d ON d.id = e.department_id
GROUP BY d.id, d.name, des.stat_date;

CREATE OR REPLACE VIEW v_employee_last_activity AS
SELECT DISTINCT ON (e.id)
    e.id AS employee_id,
    e.first_name,
    e.last_name,
    s.workstation_id,
    w.hostname,
    s.started_at,
    s.ended_at,
    s.active_seconds
FROM employees e
JOIN screen_sessions s ON s.employee_id = e.id
JOIN workstations w ON w.id = s.workstation_id
ORDER BY e.id, s.ended_at DESC;

-- Демонстрационные запросы EXPLAIN ANALYZE (запускать вручную)
-- EXPLAIN ANALYZE SELECT * FROM screen_sessions WHERE employee_id = 1 AND started_at BETWEEN '2025-01-01' AND '2025-01-31';
-- После создания индекса idx_screen_sessions_employee_date план и время выполнения улучшатся.
