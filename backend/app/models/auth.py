from __future__ import annotations

from enum import Enum


class SAPRole(str, Enum):
    CONSULTANT = "consultant"
    MANAGER = "manager"
    ADMIN = "admin"
    SERVICE = "service"

    # Hierarchy helpers
    def can_do_all(self) -> bool:
        return self == SAPRole.ADMIN

    @classmethod
    def privileged_roles(cls) -> set["SAPRole"]:
        """MANAGER and above."""
        return {cls.MANAGER, cls.ADMIN}
