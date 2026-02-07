from typing import List, Optional
from datetime import datetime


class Incident:


    def __init__(
        self,
        service_name: str,
        environment: str,
        evidences: List[str],
        status_codes: Optional[List[int]] = None,
        occurred_at: Optional[datetime] = None,
    ):
        self.service_name = service_name
        self.environment = environment
        self.evidences = evidences
        self.status_codes = status_codes or []
        self.occurred_at = occurred_at or datetime.now()
