# Constraints (Legalize)

Hard rules the codebase must respect. AI and humans should not suggest or implement code that breaks these.

## Data and schema

- **User and entity IDs**: Always string UUIDs (`db.String(36)`). Foreign keys (e.g. `Appointment.client_id`, `lawyer_id`) must match the referenced primary key type (`users.id`).
- **Roles**: Only `user` (client), `lawyer`, `admin` (from `RoleEnum`). Permission logic must use these; no ad-hoc role strings elsewhere.

## Appointments

- **Status flow**: REQUESTED → CONFIRMED → COMPLETED, or REQUESTED/CONFIRMED → CANCELLED. No transitions from COMPLETED or CANCELLED; no backward transitions (e.g. CONFIRMED → REQUESTED). Enforced in `app.domain.appointment_rules` and the appointment service.
- **Permissions**: Clients may only cancel their own appointments. Lawyers may only confirm, complete, or cancel their own. Enforcement in the service layer; routes must not bypass it.

## Architecture

- **Layers**: Routes do not call repositories directly for business flows; they call services. Services do not perform raw SQL or bypass domain rules.
- **Session in tests**: The test `db.session` must be restorable after the fixture (so Flask-SQLAlchemy teardown runs against the original session). Use the existing conftest proxy and restore pattern; do not leave `db.session` as a raw Session at context exit.

## Security and config

- **Secrets**: No API keys, passwords, or tokens in code or in ai-guidance. Use env vars and config (e.g. `Config`).
- **Auth**: Endpoints that require a role or ownership must use JWT identity and pass `actor_id` / `actor_role` into the service; the service must validate.
