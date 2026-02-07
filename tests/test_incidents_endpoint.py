from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_analyze_incident_returns_critical_for_5xx_errors():
    payload = {
        "service_name": "payment-api",
        "environment": "production",
        "evidences": [
            "Internal Server Error on POST /charge",
            "Timeout while processing payment"
        ],
        "status_codes": [500, 502]
    }

    response = client.post("/incidents/analyze", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert body["level"] == "critical"
    assert "5xx" in body["reason"].lower()
    assert body["elevated_by_context"] is False

def test_analyze_incident_returns_high_for_functional_error_in_production():
    payload = {
        "service_name": "auth-api",
        "environment": "production",
        "evidences": [
            "Login request succeeded but token is null",
            "User session not created"
        ],
        "status_codes": [200]
    }

    response = client.post("/incidents/analyze", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert body["level"] == "high"
    assert body["elevated_by_context"] is True



def test_analyze_incident_returns_medium_for_dev_environment():
    payload = {
        "service_name": "report-api",
        "environment": "development",
        "evidences": [
            "Unhandled exception while generating report"
        ],
        "status_codes": [400]
    }

    response = client.post("/incidents/analyze", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert body["level"] == "medium"
    assert body["elevated_by_context"] is False


def test_analyze_incident_fails_with_invalid_payload():
    payload = {
        "environment": "production",
        "evidences": ["Missing service_name"]
    }

    response = client.post("/incidents/analyze", json=payload)

    assert response.status_code == 422
