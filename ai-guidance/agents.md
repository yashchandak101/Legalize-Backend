# Legalize – Agent instructions

Use this when working on the Legalize codebase so behavior and conventions stay consistent.

## What this project is

- **Legalize**: production-grade LegalTech SaaS foundation for clients and lawyers (cases, appointments, auth; future: documents, payments, AI, notifications).
- **Backend**: Flask (Python), SQLAlchemy (Flask-SQLAlchemy 3), JWT, PostgreSQL via `DATABASE_URL` (SQLite for tests). Clean Architecture, DDD, horizontal scaling, path to microservices (AI, Notifications, Search).
- **Layout**: Monorepo with `backend/` as the main app; `docs/` for full design (architecture, schema, domain rules, roadmap, AI engine); `ai-guidance/` for AI and human conventions.

## Repo layout

```
legalize/
├── docs/                 # Design docs (CTO-level): architecture, schema, domain rules, roadmap, AI engine
├── ai-guidance/          # This folder: agent instructions and conventions
│   ├── agents.md         # This file – primary agent instructions
│   ├── README.md         # Purpose of ai-guidance
│   └── backend-conventions.md
├── backend/
│   ├── app/
│   │   ├── api/routes/   # HTTP endpoints (thin: parse request, call service, return JSON)
│   │   ├── core/         # config, extensions (db, migrate, jwt)
│   │   ├── domain/       # enums, business rules (e.g. appointment status transitions)
│   │   ├── models/       # SQLAlchemy models (User, Case, Appointment, BaseModel)
│   │   ├── repositories/ # DB access only (create, get, update, delete)
│   │   └── services/     # Application logic (orchestrate repo + domain rules)
│   └── tests/
│       ├── conftest.py   # pytest app + session fixtures (transaction rollback, create_all)
│       ├── unit/         # Unit tests (service/repo/model, no live HTTP)
│       └── integration/  # API tests (test client, real HTTP, same DB rollback)
│   └── ...
└── venv/                 # Python venv
```

## Conventions

- **IDs**: Use **string UUIDs** everywhere (`User.id`, `Appointment.client_id` / `lawyer_id`, etc.). No integer IDs for people or appointments.
- **Datetimes**: Prefer **timezone-aware** (`datetime.now(timezone.utc)`). Avoid `datetime.utcnow()` (deprecated).
- **Layers**: Routes → Services → Repositories. Routes do not touch `db` or models directly for business logic; services enforce permissions and domain rules; repositories do raw CRUD.
- **Session in tests**: `conftest` replaces `db.session` with a per-test transaction and a proxy so `db.session()` and `db.session.add()` both work. Restore the original session in teardown so Flask-SQLAlchemy teardown does not call `.remove()` on a plain Session.

## Running and testing

- **Tests**: From repo root, `venv/bin/python -m pytest backend/tests/ -v`; from `backend/`, `pytest tests/ -v`. Use the project venv so dependencies (e.g. `flask_sqlalchemy`) are available.
- **App**: `create_app(testing=True)` for tests; config from `app.core.config.Config`; test DB uses `DATABASE_URL` or in-memory SQLite.

## Where to add things

- **New endpoint**: Add route in `app/api/routes/`, call a method in the right **service**; keep route thin (validation, auth, then service call).
- **New business rule**: Add or extend logic in **domain/** (e.g. `appointment_rules`) or inside a **service**; do not put transition/permission logic in routes or repositories.
- **New model or field**: Add in **models/**; use `BaseModel` for `id` (UUID), `created_at`, `updated_at`; then add a migration (Flask-Migrate).
- **New test**: Prefer **unit** tests in `tests/unit/` using fixtures (e.g. real `User` rows for client/lawyer) and the conftest session so DB rolls back after each test.

## Appointment-specific

- **Status flow**: REQUESTED → CONFIRMED → COMPLETED, or REQUESTED/CONFIRMED → CANCELLED. No reverse transitions; COMPLETED/CANCELLED are terminal.
- **Who can do what**: Clients may only cancel their own appointments. Lawyers may confirm, complete, or cancel their own. Validation lives in the service using `domain/appointment_rules` and role/ownership checks.

When in doubt, follow existing patterns in `app/services/appointment_service.py`, `app/api/routes/appointment_routes.py`, and `tests/unit/test_appointment.py`.
