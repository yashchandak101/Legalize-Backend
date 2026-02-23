from enum import Enum


class RoleEnum(str, Enum):
    USER = "user"
    LAWYER = "lawyer"
    ADMIN = "admin"