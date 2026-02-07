from fastapi import APIRouter
from app.api.v1.schemas import IncidentRequest, SeverityResponse
from app.services.severity_service import SeverityService
from app.repositories.in_memory_incident_repository import InMemoryIncidentRepository
from app.use_cases.analyze_incident import AnalyzeIncidentUseCase

router = APIRouter(prefix="/incidents", tags=["Incidents"])


# LEMBRA QUE ISSO AQUI É TEMPORARIO JUMENTO, PELO AMOR DE DEUSS!!!!
severity_service = SeverityService()
incident_repository = InMemoryIncidentRepository()
# TEMPORARIO NÃO SE ESQUECE!!!


use_case = AnalyzeIncidentUseCase(
    severity_service=severity_service,
    incident_repository=incident_repository,
)


@router.post("/analyze", response_model=SeverityResponse)
def analyze_incident(request: IncidentRequest):
    severity = use_case.execute(
        service_name=request.service_name,
        environment=request.environment,
        evidences=request.evidences,
        status_codes=request.status_codes,
    )

    return {
        "level": severity.level,
        "reason": severity.reason,
        "elevated_by_context": severity.elevated_by_context,
    }
