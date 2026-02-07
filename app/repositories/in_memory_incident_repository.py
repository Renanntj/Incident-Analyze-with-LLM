from typing import List
from app.repositories.incident_repository import IncidentRepository
from app.domain.incident import Incident
from app.domain.severity import SeverityLevel


class InMemoryIncidentRepository(IncidentRepository):
    def __init__(self):
        self._incidents: List[Incident] = []

    def save(self, incident: Incident) -> None:
        self._incidents.append(incident)

    def list_all(self) -> List[Incident]:
        return self._incidents.copy()

    def find_by_severity(self, severity: SeverityLevel) -> List[Incident]:
        return [
            incident
            for incident in self._incidents
            if incident.severity.level == severity
        ]
