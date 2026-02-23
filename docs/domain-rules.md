# Legalize — Domain Rules (DDD)

Detailed domain rules by bounded context: invariants, transitions, permissions, and events. Use this to implement and test behavior; keep `ai-guidance/domain-rules.md` as a short summary for agents.

---

## 1. Bounded Contexts

| Context            | Responsibility | Key Aggregates |
|--------------------|----------------|----------------|
| **Identity & Access** | Users, roles, auth, profiles | User, LawyerProfile |
| **Case Management**   | Cases, assignment, status, comments | Case, CaseAssignment, CaseComment |
| **Scheduling**        | Appointments client–lawyer | Appointment |
| **Documents**         | Case file uploads, metadata | CaseDocument |
| **Billing**           | Payments, invoicing (stub) | Payment |
| **Notifications**     | In-app and outbound (future) | Notification |
| **AI Legal**          | Suggestions, analysis (future) | Suggestion / AnalysisResult |

---

## 2. Identity & Access

### 2.1 User

- **Invariants**
  - `email` unique, non-empty, valid format.
  - `role` ∈ { user, lawyer, admin }.
  - `password` stored hashed only; never returned in API.
- **Lifecycle**
  - Register: create with email, password, role. Default role `user`.
  - Deactivate: set `is_active = false` (admin); no hard delete of core user.
- **Authorization**
  - All authenticated actions carry `actor_id` (user id) and `actor_role` (from token). Services enforce ownership and role rules.

### 2.2 LawyerProfile

- **Invariants**
  - One profile per user with `role = lawyer`; `user_id` unique.
  - Optional: bar_number, bar_state, bio, specializations, hourly_rate_cents.
- **Rules**
  - Only lawyers can have a profile. Creating/updating a lawyer profile requires `actor_role = lawyer` and `actor_id = user_id` (or admin).
  - Profile can exist before or after first case assignment; assignment does not require a complete profile.

---

## 3. Case Management

### 3.1 Case

- **Status values**: `open` | `in_progress` | `assigned` | `closed`.
- **Transitions** (enforce in service layer):
  - open → in_progress | assigned | closed
  - in_progress → assigned | closed
  - assigned → in_progress | closed
  - closed → (terminal)
- **Invariants**
  - `user_id` (client) required. Client can have many cases.
  - `assigned_lawyer_id` optional; if set, must reference a user with `role = lawyer` and should match current active `CaseAssignment`.
- **Permissions**
  - **Client (owner)**: Create, read own, update title/description, request close; cannot assign lawyer (unless we add a “request lawyer” flow).
  - **Lawyer**: Read/comment if assigned to case; update status within allowed transitions when assigned.
  - **Admin**: Full access; can assign/reassign lawyer, change status, see all.

### 3.2 CaseAssignment

- **Invariants**
  - One active assignment per case (status = active). New assignment supersedes previous (set previous to superseded).
  - `lawyer_id` must be a user with role lawyer.
- **Rules**
  - On assignment: set `cases.assigned_lawyer_id`, optionally emit event for notifications.
  - Only admin or system can create/supersede assignments (or lawyer accept, if we add that flow).

### 3.3 CaseComment

- **Invariants**
  - `case_id` and `user_id` required. Author must have access to the case (owner, assigned lawyer, or admin).
  - `is_internal`: if true, only lawyers (and admin) see it; client does not.
- **Permissions**
  - Client: can comment on own case; cannot set `is_internal`.
  - Lawyer: can comment if assigned; can set `is_internal`.
  - Admin: can do both.

---

## 4. Scheduling (Appointments)

### 4.1 Appointment

- **Status values**: REQUESTED | CONFIRMED | COMPLETED | CANCELLED.
- **Transitions** (see `app/domain/appointment_rules`):
  - REQUESTED → CONFIRMED | CANCELLED
  - CONFIRMED → COMPLETED | CANCELLED
  - COMPLETED, CANCELLED → terminal
- **Invariants**
  - `client_id` ≠ `lawyer_id`; both must exist and client (user), lawyer (lawyer).
  - `scheduled_at` in future when creating (or allow past for back-office).
  - `duration_minutes` > 0.
- **Permissions**
  - **Client**: Create (as client_id), read own, cancel own (REQUESTED or CONFIRMED only). Cannot confirm/complete.
  - **Lawyer**: Read own, confirm, complete, or cancel own. Cannot create as client.
  - **Admin**: Full access (optional; same as lawyer for now).

### 4.2 Upcoming

- “Upcoming” = `scheduled_at > now` and status ∈ { REQUESTED, CONFIRMED }. Used for list filters and reminders.

---

## 5. Documents

### 5.1 CaseDocument

- **Invariants**
  - Belongs to one case; `uploaded_by` required. File stored externally (path/key in `storage_path`).
  - Allowed mime types and max size enforced at API/service (configurable).
- **Permissions**
  - Only users with access to the case can upload/list/delete. Delete may be restricted to uploader or admin.

---

## 6. Billing (Stub)

### 6.1 Payment

- **Status**: pending | completed | failed | refunded.
- **Rules**
  - Create via payment provider (Stripe etc.); webhook or polling updates status. No direct status change by user except refund (admin or support flow).
  - Link to `case_id` and `user_id` for display and reporting.

---

## 7. Notifications

### 7.1 Notification

- **Kinds**: e.g. case_assigned, appointment_reminder, appointment_confirmed, document_uploaded, payment_received.
- **Rules**
  - Created by core backend (or by notification service consuming events). `user_id` = recipient.
  - `read_at` set when user marks as read. Optional TTL or archive policy later.
  - Outbound (email/push) handled by worker or notification service; core may only write to `notifications` and/or outbox table.

---

## 8. Domain Events (Future Use)

For background workers and microservices, define events that the core emits (or writes to an outbox). Examples:

| Event               | Payload (minimal)        | Consumers |
|---------------------|--------------------------|-----------|
| case.assigned       | case_id, lawyer_id, assigned_by | Notifications, Analytics |
| appointment.confirmed | appointment_id, client_id, lawyer_id | Notifications, Calendar |
| appointment.reminder | appointment_id, scheduled_at | Notifications (cron/worker) |
| document.uploaded   | case_id, document_id, uploaded_by | AI service, Search index |
| payment.completed  | payment_id, case_id, user_id | Notifications, Billing |

Keep payloads small (IDs + timestamps); consumers load details via API or DB.

---

## 9. Cross-Cutting Rules

- **Idempotency**: For payments and critical mutations, support idempotency keys (e.g. header or body) and store result by key.
- **Soft delete**: Prefer `is_active` or `deleted_at` for users and key entities; hard delete only where required (e.g. GDPR).
- **Audit**: Log critical actions (status changes, assignments, payment updates) in `audit_log` or equivalent.

This document is the single source of truth for domain behavior. Implementation must enforce these rules in the application (service) layer; repositories remain dumb persistence.
