from app.domain.incident import Incident
from app.domain.severity import Severity
from app.services.severity_service import SeverityService
from app.domain.incident import Incident
from app.domain.severity import Severity
from app.domain.severity import SeverityLevel
from app.services.severity_service import SeverityService
from app.repositories.incident_repository import IncidentRepository
from typing import List, Optional
class AnalyzeIncidentUseCase:


    def __init__(self, severity_service: SeverityService):
        self.severity_service = severity_service

    def execute(
        self,
        service_name: str,
        environment: str,
        evidences: list[str],
        status_codes: list[int] | None = None,
    ) -> Severity:
        
        incident = Incident(
            service_name=service_name,
            environment=environment,
            evidences=evidences,
            status_codes=status_codes,
        )

        
        severity = self.severity_service.calculate(incident)


        return severity
class AnalyzeIncidentUseCase:
    def __init__(
        self,
        severity_service: SeverityService,
        incident_repository: IncidentRepository,
    ):
        self.severity_service = severity_service
        self.incident_repository = incident_repository

    def execute(
        self,
        service_name: str,
        environment: str,
        evidences: List[str],
        status_codes: Optional[List[int]] = None,
    ) -> Severity:
        
        severity = self.severity_service.calculate(
            evidences=evidences,
            status_codes=status_codes,
            environment=environment,
        )

        
        incident = Incident(
            service_name=service_name,
            environment=environment,
            evidences=evidences,
            status_codes=status_codes,
            severity=severity,
        )

        
        self.incident_repository.save(incident)

        return severity
