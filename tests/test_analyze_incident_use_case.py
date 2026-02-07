from app.use_cases.analyze_incident import AnalyzeIncidentUseCase
from app.services.severity_service import SeverityService
from app.repositories.in_memory_incident_repository import InMemoryIncidentRepository
from app.domain.severity import SeverityLevel


def test_should_calculate_severity_and_persist_incident():
    # Arrange
    severity_service = SeverityService()
    repository = InMemoryIncidentRepository()

    use_case = AnalyzeIncidentUseCase(
        severity_service=severity_service,
        incident_repository=repository,
    )

    # Act
    severity = use_case.execute(
        service_name="payment-api",
        environment="production",
        evidences=["timeout", "database error"],
        status_codes=[500, 502],
    )

    # Assert - severidade
    assert severity.level == SeverityLevel.CRITICAL

    # Assert - persistência
    incidents = repository.list_all()
    assert len(incidents) == 1
    assert incidents[0].service_name == "payment-api"
