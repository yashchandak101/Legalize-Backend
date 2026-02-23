# Backend conventions (Legalize)

Use when changing or adding backend code in `backend/`.

## Stack

- **Flask** (app factory in `app/__init__.py`: `create_app(testing=False)`).
- **Flask-SQLAlchemy 3** + **Flask-Migrate**; DB from `app.core.extensions` (`db`, `migrate`, `jwt`).
- **Config**: `app.core.config.Config`; `SQLALCHEMY_DATABASE_URI` from `DATABASE_URL` or in-memory SQLite.
- **Auth**: JWT (Flask-JWT-Extended); roles: `user` (client), `lawyer`, `admin` (`app.domain.enums.RoleEnum`).
- **AI**: OpenAI/Claude integration with fallback to mock; rate limiting and audit.
- **Background Workers**: Celery + Redis for async processing.

## Layers

1. **Routes** (`app/api/routes/*`): Parse request, auth, call **one** service method, return JSON. No business logic or direct repo access for non-trivial behavior.
2. **Services** (`app/services/*`): Application logic, permissions, domain rules. Call repositories and domain helpers; raise `ValueError` / `PermissionError` for bad input or denied actions.
3. **Repositories** (`app/repositories/*`): CRUD and queries only. Use `db.session` (or `db.session()` when it's a proxy); no permission or status-transition logic.
4. **Domain** (`app/domain/*`): Enums, status transition rules (e.g. `appointment_rules`), permission helpers. No DB or HTTP.
5. **Models** (`app/models/*`): SQLAlchemy models. Inherit `BaseModel` for UUID `id`, `created_at`, `updated_at`. Use `db.String(36)` for FKs to `User.id`.
6. **AI Service** (`app/services/ai_service.py`): Provider-agnostic AI interface with OpenAI/Claude support.
7. **Background Tasks** (`app/tasks/celery_tasks.py`): Celery tasks for async processing.

## IDs and types

- **User and entity IDs**: String UUIDs (`db.String(36)`), e.g. `str(uuid.uuid4())`. Type hints and APIs use `str` for IDs.
- **Foreign keys**: Match referenced primary key type (e.g. `Appointment.client_id` and `lawyer_id` are `db.String(36)` for `users.id`).

## Datetimes

- Use **timezone-aware** datetimes: `datetime.now(timezone.utc)` (and `from datetime import timezone`). Do not use `datetime.utcnow()`.
- When comparing with DB-loaded datetimes (often naive), normalize: e.g. `dt.replace(tzinfo=timezone.utc)` if naive, then compare.

## AI Integration

- **Service Pattern**: Use `AIService` for all AI calls; never call OpenAI/Claude directly from routes or repositories.
- **Rate Limiting**: Enforced in `CaseAISuggestionService` (5 case suggestions, 3 document analyses per case per day).
- **Background Processing**: Use Celery tasks (`process_ai_suggestion`, `process_document_analysis`) for long-running AI operations.
- **Fallback**: Mock provider works without API keys for development.

## Background Workers

- **Celery Setup**: Redis as broker and result backend; tasks in `app/tasks/celery_tasks.py`.
- **Async Processing**: AI suggestions and document analysis can be processed asynchronously.
- **Scheduled Tasks**: Appointment reminders run every hour via Celery beat.
- **Error Handling**: Tasks log errors and update suggestion status to 'error'.

## Session and DB in tests

- **conftest.py**: `session` fixture runs inside `app.app_context()`, calls `db.create_all()`, opens a connection and transaction, and replaces `db.session` with a **proxy** that is both callable (`db.session()`) and attribute-delegating (`db.session.add`, etc.). After the test, it closes/rollbacks and restores the original `db.session`.
- **Fixtures**: Create real `User` (and other) rows when you need valid FKs and role checks; use `db.session.add` + `db.session.flush()` so IDs are available in the same transaction.

## Query API (Flask-SQLAlchemy 3)

- Prefer **session API** for lookups: `session = db.session() if callable(db.session) else db.session`, then `session.get(Model, id)` instead of `Model.query.get(id)` (legacy).
- Listing/filtering still uses `Model.query.filter(...).all()` where the project does so.

## Appointment status and permissions

- **Status flow**: REQUESTED → CONFIRMED → COMPLETED; REQUESTED or CONFIRMED → CANCELLED. Validated in `app.domain.appointment_rules`; service calls `validate_status_transition` and enforces role/ownership.
- **Clients**: May only cancel; only their own appointments (`appointment.client_id == actor_id`).
- **Lawyers**: May confirm, complete, or cancel; only their own (`appointment.lawyer_id == actor_id`).

Keeping these conventions in mind keeps the backend consistent and testable.
