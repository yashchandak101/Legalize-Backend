# Prompting rules (Legalize)

Guidance for how to prompt or instruct AI when working on this project, so outputs stay aligned with the repo.

## When asking for features or fixes

- **Scope**: Prefer one concern per request (e.g. “add filtering by status to list appointments” or “fix session teardown in tests”). For larger work, break into steps and reference `agents.md` and `backend-conventions.md`.
- **Location**: Say where it should live when it matters (e.g. “in the appointment service”, “in `app/domain/appointment_rules`”). Otherwise the agent should infer from `agents.md` (routes vs services vs domain).
- **Tests**: Ask for or expect unit tests when adding or changing behavior (e.g. “add tests for the new filter” or “fix the failing appointment tests”). New service/domain logic should have tests in `backend/tests/unit/`.

## When asking for refactors or style

- **Conventions**: Point to “coding standards” or “backend conventions” (e.g. “make this follow our coding-standards” or “use session.get instead of query.get”). The agent should use `ai-guidance/` to resolve ambiguity.
- **IDs and datetimes**: If the agent suggests integer IDs or `utcnow()`, correct to “string UUIDs” and “timezone-aware datetimes per backend-conventions.”

## When reviewing or debugging

- **Layers**: If logic is in the wrong place (e.g. status transition in a route), ask to “move this into the service/domain per backend-conventions.”
- **Errors**: If the fix weakens permissions or skips validation, ask to “keep permission checks in the service and respect domain-rules.”

Referencing these files by name in prompts (e.g. “per agents.md”) helps the agent apply the right context.
