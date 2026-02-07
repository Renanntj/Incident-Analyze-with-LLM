from typing import List
from app.domain.incident import Incident
from app.domain.severity import Severity, SeverityLevel


class SeverityService:
    
    def calculate(self, incident: Incident) -> Severity:
        
        if self._has_critical_status_codes(incident):
            return Severity(
                level=SeverityLevel.CRITICAL,
                reason="Alta frequência de erros 5xx",
            )

        
        if self._is_production_incident(incident):
            return Severity(
                level=SeverityLevel.HIGH,
                reason="Incidente em ambiente de produção",
                elevated_by_context=True,
            )


        if self._has_error_evidences(incident):
            return Severity(
                level=SeverityLevel.MEDIUM,
                reason="Evidências indicam comportamento anômalo",
            )

        return Severity(
            level=SeverityLevel.LOW,
            reason="Impacto limitado ou não confirmado",
        )


    def _has_critical_status_codes(self, incident: Incident) -> bool:
        return any(code >= 500 for code in incident.status_codes)

    def _is_production_incident(self, incident: Incident) -> bool:
        return incident.environment.lower() == "production"

    def _has_error_evidences(self, incident: Incident) -> bool:
        keywords = ["error", "exception", "timeout", "failed"]
        return any(
            keyword in evidence.lower()
            for evidence in incident.evidences
            for keyword in keywords
        ) 
