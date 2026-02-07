from app.domain.incident import Incident
from app.domain.severity import SeverityLevel
from app.services.severity_service import SeverityService


def test_incident_with_5xx_errors_is_critical():
    incident = Incident(
        service_name="payment-api",
        environment="production",
        status_codes=[500, 502, 500],
        evidences=[
            "Internal Server Error on POST /charge",
            "Timeout while processing payment",
        ],
    )

    service = SeverityService()
    severity = service.calculate(incident)

    assert severity.level == SeverityLevel.CRITICAL
    assert "5xx" in severity.reason
    assert severity.elevated_by_context is False


def test_production_incident_with_functional_failure_is_high():
    incident = Incident(
        service_name="auth-api",
        environment="production",
        status_codes=[200, 200],
        evidences=[
            "Login request succeeded but token is null",
            "User session not created",
        ],
    )

    service = SeverityService()
    severity = service.calculate(incident)

    assert severity.level == SeverityLevel.HIGH
    assert "produção" in severity.reason.lower()
    assert severity.elevated_by_context is True


def test_development_incident_with_errors_is_medium():
    incident = Incident(
        service_name="report-api",
        environment="development",
        status_codes=[400],
        evidences=[
            "Unhandled exception while generating report",
            "NullPointerException on line 42",
        ],
    )

    service = SeverityService()
    severity = service.calculate(incident)

    assert severity.level == SeverityLevel.MEDIUM
    assert severity.elevated_by_context is False
