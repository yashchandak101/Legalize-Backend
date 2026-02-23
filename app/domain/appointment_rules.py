class InvalidAppointmentStatusTransition(Exception):
    pass


ALLOWED_TRANSITIONS = {
    "REQUESTED": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["COMPLETED", "CANCELLED"],
    "COMPLETED": [],
    "CANCELLED": [],
}


def validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Validates whether appointment status can move
    from current_status -> new_status.

    Raises:
        InvalidAppointmentStatusTransition
    """

    if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
        raise InvalidAppointmentStatusTransition(
            f"Cannot change appointment status from "
            f"{current_status} to {new_status}"
        )