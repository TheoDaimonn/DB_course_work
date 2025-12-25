# Система учета экранного времени сотрудников (Python + PostgreSQL)

Курсовой проект по дисциплине "Базы данных". Проект представляет собой backend-приложение на Python (FastAPI) с базой данных PostgreSQL для учета экранного времени сотрудников.

## Запуск проекта

1. Установите Docker и docker-compose.
2. В корне проекта выполните:

   ```bash
   docker compose up --build
   ```

3. После запуска:
   - База данных будет инициализирована скриптом `sql/init.sql` (схема `screentime`, таблицы, функции, триггеры, представления, индексы).
   - Backend будет доступен по адресу `http://localhost:8000`.
   - Swagger UI (документация API) — по адресу `http://localhost:8000/docs`.

## Генерация тестовых данных

После запуска контейнеров можно сгенерировать реалистичные тестовые данные:

```bash
docker-compose exec backend python -m app.scripts.generate_test_data
```

Скрипт создаст:
- 4 отдела, 5 должностей, 5 приложений;
- ~200 сотрудников и 200 рабочих станций;
- за последние 30 дней по нескольку сессий экранного времени на каждого сотрудника (в сумме 5000+ строк в `screen_sessions`).

Триггеры автоматически заполнят агрегированную таблицу `daily_employee_stats`.

## Основные сущности базы данных

- `departments` — подразделения компании.
- `positions` — должности.
- `users` — учетные записи пользователей системы (админ, менеджер, просмотр).
- `employees` — сотрудники (ФИО, email, отдел, должность, дата найма).
- `workstations` — рабочие станции (hostname, инвентарный номер, ОС, отдел).
- `applications` — приложения (код, категория, продуктивность).
- `employee_workstations` — связь N:M сотрудник–рабочая станция.
- `screen_sessions` — транзакционная таблица сессий экранного времени (основной объем данных).
- `session_application_usage` — использование приложений в рамках сессии.
- `daily_employee_stats` — агрегированная статистика по сотруднику за день.
- `audit_log` — журнал аудита изменений (INSERT/UPDATE/DELETE).
- `batch_import_logs` — логирование массовых импортов.

## Триггеры и функции

- `trg_write_audit_log` — общий триггер аудита для таблиц `employees`, `workstations`, `screen_sessions`, `applications`.
- `trg_update_daily_stats` + функция `fn_recalculate_daily_employee_stat` — автоматический пересчет суточной статистики при изменении `screen_sessions`.
- Скалярная функция `fn_employee_daily_load(employee_id, date)` — суммарное экранное время сотрудника за день (в часах).
- Табличная функция `fn_top_overworked_employees(date_from, date_to, min_hours_per_day)` — сотрудники с превышением среднего экранного времени.
- Табличная функция `fn_department_load(date_from, date_to)` — нагрузка по отделам.

## Представления (VIEW)

- `v_employee_daily_stats` — статистика по сотруднику с подстановкой ФИО, отдела, должности.
- `v_department_daily_stats` — суточная статистика по отделам.
- `v_employee_last_activity` — последняя сессия активности каждого сотрудника.

## API (FastAPI + Swagger)

Базовый URL: `http://localhost:8000`.

Основные группы эндпоинтов:

- `/api/departments` — CRUD по отделам.
- `/api/employees` — CRUD по сотрудникам.
- `/api/workstations` — CRUD по рабочим станциям.
- `/api/applications` — CRUD по приложениям.
- `/api/sessions` — создание и просмотр сессий экранного времени.
- `/api/reports/*` — отчеты на чистом SQL (JOIN, агрегаты, вызов функций):
  - `/api/reports/employee-daily` — статистика по сотруднику за день (VIEW `v_employee_daily_stats`).
  - `/api/reports/department-daily` — статистика по отделам за день (VIEW `v_department_daily_stats`).
  - `/api/reports/last-activity` — последняя активность сотрудника (VIEW `v_employee_last_activity`).
  - `/api/reports/top-overworked` — вызов функции `fn_top_overworked_employees`.
  - `/api/reports/department-load` — вызов функции `fn_department_load`.
- `/api/batch-import/sessions` — массовый импорт сессий экранного времени с логированием в `batch_import_logs`.

Полное описание запросов, параметров и ответов доступно в Swagger UI (`/docs`).

## Оптимизация и EXPLAIN ANALYZE

В файле `sql/init.sql` приведен пример запроса с `EXPLAIN ANALYZE` к таблице `screen_sessions` по полям `employee_id` и `started_at`. Индекс `idx_screen_sessions_employee_date` значительно ускоряет такие выборки по сравнению с полным сканированием таблицы.

## Проверка соответствия техническому заданию

- **Структура БД**: 12 таблиц, связи 1:1, 1:N, N:M.
- **Ограничения целостности**: повсюду используются `PRIMARY KEY`, `FOREIGN KEY` с каскадным обновлением/удалением, `UNIQUE`, `CHECK`, `NOT NULL`.
- **Объём данных**: скрипт генерации данных создает сотни записей в справочниках и десятки тысяч записей в транзакционной таблице `screen_sessions` (минимум 5000+, на практике ≈ 500 × 30 × 3 = 45000 сессий).
- **SQL-функциональность**: реализованы триггеры аудита и обновления агрегатов, скалярная и табличные функции, представления.
- **Интеграция с backend**: CRUD через ORM (SQLAlchemy), сложные отчеты через чистый SQL.
- **Batch-импорт**: эндпоинт `/api/batch-import/sessions` с логированием результатов в `batch_import_logs`.
- **Документация API**: Swagger/OpenAPI автоматически генерируется FastAPI.
- **Контейнеризация**: `docker-compose.yml` поднимает PostgreSQL и backend; схема БД инициализируется автоматически.
