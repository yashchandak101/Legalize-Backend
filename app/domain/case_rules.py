"""
Case status transition rules (domain layer).
Enforce in CaseService when updating case status.
"""
from typing import List

# Canonical status values (match docs/domain-rules.md)
STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_ASSIGNED = "assigned"
STATUS_CLOSED = "closed"

CASE_STATUS_CHOICES: List[str] = [
    STATUS_OPEN,
    STATUS_IN_PROGRESS,
    STATUS_ASSIGNED,
    STATUS_CLOSED,
]

ALLOWED_TRANSITIONS = {
    STATUS_OPEN: [STATUS_IN_PROGRESS, STATUS_ASSIGNED, STATUS_CLOSED],
    STATUS_IN_PROGRESS: [STATUS_ASSIGNED, STATUS_CLOSED],
    STATUS_ASSIGNED: [STATUS_IN_PROGRESS, STATUS_CLOSED],
    STATUS_CLOSED: [],
}


class InvalidCaseStatusTransition(Exception):
    """Raised when a case status transition is not allowed."""
    pass


def validate_case_status_transition(current_status: str, new_status: str) -> None:
    """
    Validate that a case can move from current_status to new_status.
    Raises InvalidCaseStatusTransition if not allowed.
    """
    if new_status not in CASE_STATUS_CHOICES:
        raise InvalidCaseStatusTransition(
            f"Invalid status '{new_status}'. Must be one of {CASE_STATUS_CHOICES}"
        )
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise InvalidCaseStatusTransition(
            f"Cannot change case status from {current_status} to {new_status}"
        )
