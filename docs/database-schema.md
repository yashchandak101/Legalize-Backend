# Legalize — Database Schema

Full schema design for production: tables, fields, relations, and indexes. Aligns with current models and extends for lawyer profile, case assignment, comments, documents, payments, notifications, and AI suggestions.

---

## 1. Conventions

- **Primary keys**: UUID `CHAR(36)` / `VARCHAR(36)` for all entities.
- **Foreign keys**: Same type as referenced PK. `ON DELETE` explicit (CASCADE, SET NULL, or RESTRICT).
- **Timestamps**: `created_at`, `updated_at` in UTC; timezone-aware in application.
- **Indexes**: On FKs, status, and frequently filtered/sorted columns (e.g. `user_id`, `status`, `scheduled_at`).
- **Naming**: `snake_case`; tables plural where it reads well (`users`, `cases`, `appointments`).

---

## 2. Entity-Relation Overview

```
users ──┬──< cases (user_id)
        ├──< appointments (client_id, lawyer_id)
        ├──< lawyer_profiles (1:1 for role=lawyer)
        ├──< notifications (user_id)
        └── (optional) payments (user_id)

cases ───┬──< case_assignments (case_id, lawyer_id)
         ├──< case_comments (case_id)
         ├──< case_documents (case_id)
         ├──< payments (case_id)
         └──< case_ai_suggestions (case_id)

appointments ── (standalone; client_id, lawyer_id → users)
```

---

## 3. Tables (Detailed)

### 3.1 `users`

| Column       | Type         | Nullable | Default | Description |
|-------------|--------------|----------|---------|-------------|
| id          | VARCHAR(36)  | NO       | uuid    | PK, UUID |
| email       | VARCHAR(120) | NO      | —       | Unique |
| password    | VARCHAR(255) | NO      | —       | Hashed |
| role        | VARCHAR(20)  | NO      | 'user'  | user | lawyer | admin |
| name        | VARCHAR(120) | YES     | —       | Display name |
| phone       | VARCHAR(30)  | YES     | —       | Optional |
| avatar_url  | VARCHAR(500) | YES     | —       | Optional profile image |
| is_active   | BOOLEAN      | NO      | true    | Soft disable |
| created_at  | TIMESTAMPTZ  | NO      | now()   | |
| updated_at  | TIMESTAMPTZ  | NO      | now()   | |

- **Unique**: `email`.
- **Indexes**: `email`, `role`, `is_active`.

---

### 3.2 `lawyer_profiles`

Extends users with role=lawyer. 1:1 with `users`.

| Column           | Type         | Nullable | Default | Description |
|------------------|--------------|----------|---------|-------------|
| id               | VARCHAR(36)  | NO       | uuid    | PK, UUID |
| user_id          | VARCHAR(36)  | NO       | —       | FK → users.id, UNIQUE |
| bar_number       | VARCHAR(50)  | YES     | —       | Bar/license number |
| bar_state        | VARCHAR(10)  | YES     | —       | State/jurisdiction |
| bio              | TEXT         | YES     | —       | |
| specializations  | VARCHAR(255) | YES     | —       | Comma-sep or JSON array later |
| hourly_rate_cents | INTEGER      | YES     | —       | Optional; for display/billing |
| created_at       | TIMESTAMPTZ  | NO      | now()   | |
| updated_at       | TIMESTAMPTZ  | NO      | now()   | |

- **Unique**: `user_id`.
- **Indexes**: `user_id`.

---

### 3.3 `cases`

| Column    | Type         | Nullable | Default | Description |
|-----------|--------------|----------|---------|-------------|
| id        | SERIAL       | NO       | —       | PK (legacy integer) |
| user_id   | VARCHAR(36)  | NO       | —       | FK → users.id (client) |
| title     | VARCHAR(255) | NO       | —       | |
| description | TEXT       | NO       | —       | |
| status    | VARCHAR(50)  | NO       | 'open'  | open | in_progress | assigned | closed |
| assigned_lawyer_id | VARCHAR(36) | YES | —   | FK → users.id (denormalized for quick access) |
| created_at | TIMESTAMPTZ | NO      | now()   | |
| updated_at | TIMESTAMPTZ | NO      | now()   | |

- **Indexes**: `user_id`, `status`, `assigned_lawyer_id`.
- **Note**: `assigned_lawyer_id` can be derived from `case_assignments`; denormalized for listing/filtering.

---

### 3.4 `case_assignments`

History and current assignment of lawyers to cases (supports reassignment and audit).

| Column     | Type         | Nullable | Default | Description |
|------------|--------------|----------|---------|-------------|
| id         | VARCHAR(36)  | NO       | uuid    | PK |
| case_id    | INTEGER      | NO       | —       | FK → cases.id |
| lawyer_id  | VARCHAR(36)  | NO       | —       | FK → users.id |
| assigned_at| TIMESTAMPTZ  | NO       | now()   | |
| assigned_by| VARCHAR(36)  | YES     | —       | FK → users.id (admin or system) |
| status     | VARCHAR(20)  | NO       | 'active'| active | superseded |
| notes      | TEXT         | YES     | —       | |

- **Indexes**: `case_id`, `lawyer_id`, `status`.
- **Unique**: One active assignment per case (enforced in app or partial unique index).

---

### 3.5 `appointments`

Already implemented; summarized for completeness.

| Column           | Type         | Nullable | Default     | Description |
|------------------|--------------|----------|-------------|-------------|
| id               | VARCHAR(36)  | NO       | uuid        | PK |
| client_id        | VARCHAR(36)  | NO       | —           | FK → users.id |
| lawyer_id        | VARCHAR(36)  | NO       | —           | FK → users.id |
| scheduled_at     | TIMESTAMPTZ  | NO       | —           | |
| duration_minutes | INTEGER      | NO       | 30          | |
| meeting_link     | VARCHAR(500) | YES     | —           | |
| notes            | TEXT         | YES     | —           | |
| status           | VARCHAR(20)  | NO       | 'REQUESTED' | REQUESTED | CONFIRMED | COMPLETED | CANCELLED |
| created_at       | TIMESTAMPTZ  | NO       | now()       | |
| updated_at       | TIMESTAMPTZ  | NO       | now()       | |

- **Indexes**: `client_id`, `lawyer_id`, `scheduled_at`, `status`.
- **Check**: `status IN (...)`.

---

### 3.6 `case_comments`

Threaded or flat comments on a case (client, lawyer, admin).

| Column     | Type         | Nullable | Default | Description |
|------------|--------------|----------|---------|-------------|
| id         | VARCHAR(36)  | NO       | uuid    | PK |
| case_id    | INTEGER      | NO       | —       | FK → cases.id |
| user_id    | VARCHAR(36)  | NO       | —       | FK → users.id (author) |
| parent_id  | VARCHAR(36)  | YES     | —       | FK → case_comments.id (for threading) |
| body       | TEXT         | NO       | —       | |
| is_internal| BOOLEAN      | NO       | false   | Lawyer-only visibility |
| created_at | TIMESTAMPTZ  | NO       | now()   | |
| updated_at | TIMESTAMPTZ  | NO       | now()   | |

- **Indexes**: `case_id`, `user_id`, `parent_id`, `created_at`.

---

### 3.7 `case_documents`

Metadata for uploaded files (store blob in object storage; DB holds reference and metadata).

| Column       | Type         | Nullable | Default | Description |
|--------------|--------------|----------|---------|-------------|
| id           | VARCHAR(36)  | NO       | uuid    | PK |
| case_id      | INTEGER      | NO       | —       | FK → cases.id |
| uploaded_by  | VARCHAR(36)  | NO       | —       | FK → users.id |
| filename     | VARCHAR(255) | NO       | —       | Original name |
| storage_path | VARCHAR(500) | NO       | —       | S3/key or path |
| mime_type    | VARCHAR(100) | YES     | —       | |
| size_bytes   | INTEGER      | YES     | —       | |
| created_at   | TIMESTAMPTZ  | NO       | now()   | |
| updated_at   | TIMESTAMPTZ  | NO       | now()   | |

- **Indexes**: `case_id`, `uploaded_by`, `created_at`.

---

### 3.8 `payments` (stub for later)

| Column       | Type         | Nullable | Default | Description |
|--------------|--------------|----------|---------|-------------|
| id           | VARCHAR(36)  | NO       | uuid    | PK |
| case_id      | INTEGER      | YES     | —       | FK → cases.id (optional) |
| user_id      | VARCHAR(36)  | NO       | —       | Payer (FK → users.id) |
| amount_cents | INTEGER      | NO       | —       | |
| currency     | CHAR(3)      | NO       | 'USD'   | |
| status       | VARCHAR(20)  | NO       | —       | pending | completed | failed | refunded |
| external_id  | VARCHAR(100) | YES     | —       | Stripe/payment provider id |
| created_at   | TIMESTAMPTZ  | NO       | now()   | |
| updated_at   | TIMESTAMPTZ  | NO       | now()   | |

- **Indexes**: `case_id`, `user_id`, `status`, `external_id`.

---

### 3.9 `notifications` (in-app / outbox for worker)

| Column       | Type         | Nullable | Default | Description |
|--------------|--------------|----------|---------|-------------|
| id           | VARCHAR(36)  | NO       | uuid    | PK |
| user_id      | VARCHAR(36)  | NO       | —       | FK → users.id (recipient) |
| kind         | VARCHAR(50)  | NO       | —       | case_assigned | appointment_reminder | etc. |
| title        | VARCHAR(255) | YES     | —       | |
| body         | TEXT         | YES     | —       | |
| payload      | JSONB        | YES     | —       | Links, entity ids |
| read_at      | TIMESTAMPTZ  | YES     | —       | |
| created_at   | TIMESTAMPTZ  | NO       | now()   | |

- **Indexes**: `user_id`, `read_at`, `created_at`, `kind`.

---

### 3.11 `case_ai_suggestions`

| Column             | Type         | Nullable | Default | Description |
|--------------------|--------------|----------|---------|-------------|
| id                 | VARCHAR(36)  | NO       | uuid    | PK |
| case_id            | VARCHAR(36)  | NO       | —       | FK → cases.id |
| user_id            | VARCHAR(36)  | NO       | —       | FK → users.id (requester) |
| suggestion_type    | VARCHAR(50)  | NO       | case_suggestions | case_suggestions | document_analysis |
| status             | VARCHAR(20)  | NO       | pending | pending | completed | error |
| provider           | VARCHAR(50)  | YES     | —       | openai | anthropic | mock |
| model              | VARCHAR(100) | YES     | —       | gpt-4 | claude-3-sonnet | mock |
| suggestions        | JSONB        | YES     | —       | AI response data |
| error_message      | TEXT         | YES     | —       | Error if failed |
| request_data       | JSONB        | YES     | —       | Original request data |
| processing_time_ms | INTEGER      | YES     | —       | Processing time in ms |
| created_at         | TIMESTAMPTZ  | NO       | now()   | |
| updated_at         | TIMESTAMPTZ  | NO       | now()   | |

- **Indexes**: `case_id`, `user_id`, `suggestion_type`, `status`, `created_at`.
- **Rate limiting**: Enforced at service level (5 case suggestions, 3 document analyses per case per day).

---

### 3.12 `audit_log` (optional, for critical actions)

| Column     | Type         | Nullable | Default | Description |
|------------|--------------|----------|---------|-------------|
| id         | BIGSERIAL    | NO       | —       | PK |
| user_id    | VARCHAR(36)  | YES     | —       | Actor |
| action     | VARCHAR(100) | NO       | —       | e.g. case.status_changed |
| entity_type| VARCHAR(50)  | YES     | —       | case | appointment | user |
| entity_id  | VARCHAR(36)  | YES     | —       | |
| old_value  | JSONB        | YES     | —       | |
| new_value  | JSONB        | YES     | —       | |
| created_at | TIMESTAMPTZ  | NO       | now()   | |

- **Indexes**: `user_id`, `entity_type`, `entity_id`, `created_at`.

---

## 4. Migration Strategy

1. **Current → this schema**: Add new tables (`lawyer_profiles`, `case_assignments`, `case_comments`, `case_documents`, `payments`, `notifications`, `case_ai_suggestions`, `audit_log`) via Flask-Migrate. Add `users.name`, `users.phone`, `users.avatar_url`, `users.is_active` and `cases.assigned_lawyer_id` in migrations; keep existing PKs and FKs.
2. **Case.id**: All primary keys are now UUID for consistency.
3. **Indexes**: Add in same migrations as tables or in dedicated index migrations; avoid long locks (CONCURRENTLY in PostgreSQL where needed).
4. **AI Features**: Requires Redis and Celery setup for background processing.

This schema is the single source of truth for persistence. Implement models and repositories to match; use domain rules for invariants and transitions.
