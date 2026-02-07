from pydantic import BaseModel
from typing import List, Optional
from app.domain.severity import SeverityLevel


class IncidentRequest(BaseModel):
    service_name: str
    environment: str
    evidences: List[str]
    status_codes: Optional[List[int]] = None


class SeverityResponse(BaseModel):
    level: SeverityLevel
    reason: str
    elevated_by_context: bool

