# Legalize — Implementation Roadmap (CTO-Level)

Step-by-step backend implementation that preserves Clean Architecture, enables horizontal scaling and background workers, and keeps a clear path to AI and microservices. Each phase has concrete deliverables and acceptance criteria.

---

## Phase 0: Current State (Done)

- [x] Flask app factory, config, PostgreSQL/SQLite
- [x] User model (UUID, email, password, role: user | lawyer | admin)
- [x] Case model (client-owned, status: open/assigned/closed)
- [x] Appointment model (client–lawyer, status lifecycle)
- [x] JWT auth (register, login, role in token)
- [x] Case CRUD API (with ownership)
- [x] Appointment API (create as client, list, get, update status; role from JWT)
- [x] Service/repository/domain layer split
- [x] Unit + integration tests, ai-guidance and conventions
- [x] Architecture and schema design (this docs set)

**Gap vs schema**: User has no `name`, `phone`, `avatar_url`, `is_active`. Case has no `assigned_lawyer_id`. No `lawyer_profiles`, `case_assignments`, comments, documents, payments, notifications.

---

## Phase 1: Foundation Hardening (Next)

**Goal**: Align codebase with [database-schema](database-schema.md) and [domain-rules](domain-rules.md) for Identity and Case; no new features yet.

### 1.1 User and config

- Add columns: `name`, `phone`, `avatar_url`, `is_active` (default true). Migration only; API can expose name/phone in profile later.
- Env: ensure `JWT_SECRET_KEY` length ≥ 32 in production; document in README or config.

### 1.2 Case status and assignment field

- Normalize case status: `open` | `in_progress` | `assigned` | `closed` (match domain-rules). Migration + CaseService + any routes that set status.
- Add `assigned_lawyer_id` (nullable FK to users). Migration; set only via assignment flow in Phase 2.
- Enforce case status transitions in domain (e.g. `app/domain/case_rules.py`) and CaseService.

### 1.3 Validation and errors

- Add request validation layer (e.g. marshmallow or pydantic) for auth and case payloads; return 400 with clear messages.
- Standardize API error shape: `{ "error": "<message>", "code": "<optional>" }`. No stack traces in production.

### 1.4 Logging and safety

- Structured logging (request_id, user_id, action) for auth and case/appointment mutations.
- Health endpoint: `GET /health` (DB ping optional). For load balancer and later K8s.

**Deliverables**: Migrations applied; case status and assignment field in place; validation on key endpoints; logging and health check. All existing tests pass.

---

## Phase 2: Lawyer Profile and Case Assignment

**Goal**: Lawyers have profiles; admins (or system) can assign cases to lawyers; case list/filter by assignment.

### 2.1 LawyerProfile

- Table `lawyer_profiles` per schema (user_id, bar_number, bar_state, bio, specializations, hourly_rate_cents, timestamps).
- LawyerProfileRepository; LawyerProfileService (create/update/get by user_id). Only lawyer or admin can create/update.
- API: `GET/PUT /api/users/me/profile` (lawyer only); optional `GET /api/lawyers/:id/profile` (public for booking).

### 2.2 Case assignment

- Table `case_assignments` (case_id, lawyer_id, assigned_at, assigned_by, status: active | superseded).
- CaseAssignmentService: assign(case_id, lawyer_id, actor_id) → create new assignment, supersede previous, set cases.assigned_lawyer_id. Restrict to admin (or lawyer accept if desired).
- API: `POST /api/cases/:id/assign` (body: lawyer_id), `GET /api/cases/:id/assignments` (history). Enforce case access by role.

### 2.3 Case status and permissions

- When assigning, set case status to `assigned` if not already. When unassigning (supersede, no new lawyer), set to `open` or `in_progress` per product rule.
- Case list: filter by `assigned_lawyer_id` for lawyer view; admin sees all. Permissions: client sees own; lawyer sees assigned; admin sees all.

**Deliverables**: Lawyer profiles and case assignment APIs; migrations; unit and integration tests. RBAC documented in domain-rules.

---

## Phase 3: Comments and Documents

**Goal**: Case comments (with optional internal flag); document metadata and upload (file to object storage or disk; DB stores metadata).

### 3.1 Case comments

- Table `case_comments` per schema. CaseCommentRepository and CaseCommentService; enforce case access and internal visibility.
- API: `GET/POST /api/cases/:id/comments`; optional `PATCH/DELETE` for own comment. Body: `body`, `is_internal` (lawyer/admin only).

### 3.2 Case documents

- Table `case_documents`; storage_path points to S3 or local path. Upload flow: validate file type/size, store file, insert row.
- CaseDocumentService + repository. API: `POST /api/cases/:id/documents` (multipart), `GET /api/cases/:id/documents`, `GET /api/documents/:id` (signed URL or redirect). Delete: soft or hard per policy.

**Deliverables**: Comments and documents APIs; migrations; tests. Optional: background job to virus-scan or generate thumbnails (stub task name for later worker).

---

## Phase 4: Payments and Notifications (Stub → Real)

**Goal**: Payment table and minimal flow (e.g. Stripe); notifications table and in-app list; outbound email/push via worker later.

### 4.1 Payments

- Table `payments` per schema. PaymentService: create intent (call Stripe), confirm via webhook or callback; update status. API: `POST /api/cases/:id/payments` (create intent), `GET /api/payments` (own). Webhook endpoint for provider.

### 4.2 Notifications

- Table `notifications` per schema. NotificationService: create(user_id, kind, title, body, payload); list by user (paginated); mark read.
- API: `GET /api/notifications`, `PATCH /api/notifications/:id/read`. Create notifications from case assignment and appointment events (sync for now).
- Later: Celery task to send email/push from same events; notification service consumes queue.

**Deliverables**: Payments and notifications tables and APIs; Stripe (or one provider) integrated; tests. Document webhook idempotency.

---

## Phase 5: AI and Background Workers 

**Goal**: AI legal engine interface (internal or HTTP); Celery + Redis for async jobs.

### 5.1 AI legal engine (design + first use case) 

- Define **AI Service interface**: input (case_id, doc_ids, prompt_type), output (suggestions or analysis result). Implemented as internal module with OpenAI/Claude API support.
- One concrete use case: “suggestions for case” (based on title/description). Store result in `case_ai_suggestions` table; rate limit and audit implemented.
- API: `POST /api/cases/:id/suggestions` (async or sync), `GET /api/cases/:id/suggestions`. Only case participants.
- Document analysis: `POST /api/documents/:id/analyze` for AI-powered document analysis.

### 5.2 Background workers 

- Introduce Redis and Celery. Config: `CELERY_BROKER_URL`, `REDIS_URL`.
- Tasks: `send_appointment_reminder`, `index_case_for_search` (stub), `process_ai_suggestion`, `process_document_analysis`. Call from services with `task.delay(...)`.
- Deployment: workers run as separate process; same codebase.
- Scheduled tasks: Appointment reminders every hour.

**Deliverables**: AI suggestion endpoint and integration; Celery worker running; multiple tasks implemented. Rate limiting and audit complete.

---

## Phase 6: Scale and Extract (Future)

- **Read replicas**: Route read-only case/list and search queries to replica if needed.
- **Search**: Add Elasticsearch; index cases/documents via worker; search API in core or dedicated search service.
- **Extract AI service**: Move AI calls and prompts to a separate service; core calls it via HTTP or queue.
- **Extract notification service**: Move email/push sending to a service consuming events from core (or from queue).

---

## How to Use This Roadmap

- **Implement in order**: Phase 1 → 2 → 3 → 4 → 5 → 6. Each phase merges to main with tests and migrations.
- **Design first**: For each feature, align with [database-schema](database-schema.md) and [domain-rules](domain-rules.md); then implement in services/repositories and expose via API.
- **Test**: Unit tests for domain and services; integration tests for new endpoints; keep existing tests green.
- **Document**: Update ai-guidance and README when adding new domains or conventions. Keep architecture and schema docs as source of truth.

This is the CTO-level plan. We build like a CTO: design full schema and domain rules, then implement step-by-step with clear phases and deliverables.
