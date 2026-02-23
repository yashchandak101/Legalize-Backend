# Domain rules (Legalize)

Business rules that the application must enforce. Implement in `app/domain/` and services; do not duplicate or override in routes or repositories.

## Appointments

- **Status lifecycle**  
  - Allowed transitions (see `app/domain/appointment_rules`):
    - REQUESTED → CONFIRMED | CANCELLED  
    - CONFIRMED → COMPLETED | CANCELLED  
    - COMPLETED → (none)  
    - CANCELLED → (none)  
  - Any other transition is invalid. Services must call `validate_status_transition` before updating; invalid transitions raise and are surfaced as `ValueError` to the API.

- **Who can change status**  
  - **Client (role `user`)**: May only set status to CANCELLED, and only for appointments where `client_id == actor_id`. Any other action or wrong appointment → `PermissionError`.  
  - **Lawyer (role `lawyer`)**: May set CONFIRMED, COMPLETED, or CANCELLED, and only for appointments where `lawyer_id == actor_id`. Any other action or wrong appointment → `PermissionError`.  
  - **Admin**: Not yet special-cased; can be extended in the same service layer without changing these rules.

- **Upcoming**: “Upcoming” = `scheduled_at > now` and status in (REQUESTED, CONFIRMED). Completed and cancelled are excluded.

## Cases

- **Status lifecycle**
  - Allowed transitions: OPEN → ASSIGNED → IN_PROGRESS → COMPLETED | CLOSED
  - Any other transition is invalid and must raise `ValueError`.

- **Assignment rules**
  - Only admins or lawyers can assign cases to lawyers
  - A case can have only one active assignment at a time
  - Case status automatically changes to ASSIGNED when lawyer is assigned

## Users and roles

- **Roles**: `user` (client), `lawyer`, `admin` from `RoleEnum`. Used for permission checks; no other role strings in business logic.
- **Identity**: Actions are performed by an actor identified by `actor_id` (user id) and `actor_role`. Services receive these from the API layer (e.g. JWT) and enforce ownership and allowed actions.

## Payments

- **Status lifecycle**: PENDING → COMPLETED | FAILED | REFUNDED
- **Authorization**: Users can only access their own payments; admins can access all payments
- **Refunds**: Only completed payments can be refunded; full or partial refunds allowed

## Notifications

- **Access**: Users can only access their own notifications; admins can access all
- **Read status**: Users can mark their own notifications as read
- **Event-driven**: Created automatically for case assignments, payments, comments, documents

## AI Suggestions

- **Rate limiting**: 5 case suggestions, 3 document analyses per case per day per user
- **Authorization**: Users can only create suggestions for cases they have access to
- **Processing**: Can be synchronous or asynchronous via Celery
- **Providers**: OpenAI, Anthropic, or mock fallback

## Comments

- **Internal comments**: Only lawyers and admins can create/view internal comments
- **Public comments**: All case participants can create/view public comments
- **Authorization**: Users can only comment on cases they have access to

## Documents

- **Access**: Users can only access documents for cases they have access to
- **Upload**: Only authenticated users can upload documents to accessible cases
- **Deletion**: Soft delete (mark as deleted) to preserve audit trail

## Consistency

- New features that touch appointments must follow the same status and permission rules. New statuses or transitions require updates to `app/domain/appointment_rules` and to `domain-rules.md` and any related ai-guidance.
- New features must follow the same status and permission patterns
- New statuses or transitions require updates to domain rules and documentation
- All authorization checks must be implemented in services, not routes or repositories
