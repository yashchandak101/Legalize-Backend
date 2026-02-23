# Coding standards (Legalize)

Apply when writing or reviewing code in this repo.

## Python / Backend

- **Imports**: Prefer absolute from app root for domain/config (`from app.domain.enums import RoleEnum`). Use relative within a package (`from ..core.extensions import db`). Group: stdlib → third-party → local; alphabetical within groups.
- **Types**: Use type hints for function args and return values, especially in services and repositories (`str`, `Optional[T]`, `List[T]`).
- **Errors**: Use built-ins deliberately: `ValueError` for invalid input or not-found, `PermissionError` for authz. In services, translate domain exceptions (e.g. `InvalidAppointmentStatusTransition`) into `ValueError` or `PermissionError` for the API layer.
- **Datetimes**: Timezone-aware only. `datetime.now(timezone.utc)`; never `datetime.utcnow()`. When comparing with DB-loaded datetimes (often naive), normalize before compare.
- **IDs**: String UUIDs everywhere for users and entities. No integer IDs for people or appointments.

## Structure

- **Routes**: Thin. Parse body/query, resolve identity (e.g. JWT), call one service method, return JSON. No business or DB logic.
- **Services**: All business and permission logic. Call repositories and domain helpers; raise clear exceptions.
- **Repositories**: CRUD and queries only. Use `db.session` / `db.session()`; no permission or status rules.
- **Tests**: Prefer unit tests with real DB fixtures (e.g. `User` rows) and transaction rollback. One clear assertion focus per test; use classes to group related cases.

## Style

- Docstrings for public service/repository methods and non-obvious domain functions. Keep them one short sentence when that’s enough.
- Prefer explicit over clever. Simple conditionals and early returns over deep nesting.
