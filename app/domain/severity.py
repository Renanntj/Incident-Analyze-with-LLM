from enum import Enum


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Severity:
    def __init__(
        self,
        level: SeverityLevel,
        reason: str,
        elevated_by_context: bool = False,
    ):
        self.level = level
        self.reason = reason
        self.elevated_by_context = elevated_by_context
