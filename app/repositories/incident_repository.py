from abc import ABC, abstractmethod
from typing import List
from app.domain.incident import Incident
from app.domain.severity import SeverityLevel


class IncidentRepository(ABC):
    @abstractmethod
    def save(self, incident: Incident) -> None:
        pass

    @abstractmethod
    def list_all(self) -> List[Incident]:
        pass

    @abstractmethod
    def find_by_severity(self, severity: SeverityLevel) -> List[Incident]:
        pass
