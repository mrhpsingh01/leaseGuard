"""
Integration tests for FastAPI endpoints
"""

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["statutes_loaded"] == 5

def test_sample_lease_endpoint():
    resp = client.get("/api/v1/leases/sample")
    assert resp.status_code == 200
    data = resp.json()
    assert data["monthly_rent"] == 1150.00
    assert data["security_deposit"] == 2800.00
    assert data["deposit_excess"] == 500.00
    assert data["unenforceable_clauses_count"] == 5
    assert len(data["flagged_risks"]) == 5
    assert len(data["pages"]) == 3
    assert data["telemetry"]["statutes_evaluated"] == 5

def test_dispute_endpoints():
    eval_resp = client.post("/api/v1/disputes/evaluate", json={
        "move_out_date": "2024-07-31",
        "inspection_list_date": "2024-08-07",
        "current_date": "2024-09-10",
        "total_withheld": 850.00
    })
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["forfeiture_triggered"] is True
    assert eval_data["treble_damages_amount"] == 2550.00

    pdf_resp = client.post("/api/v1/disputes/demand-letter", json={
        "evaluation": {
            "tenant_name": "Alex M. Jordan",
            "landlord_name": "Lakeside Student Commons LLC",
            "property_address": "150 Riverbend Pkwy, Unit 304B, Athens, GA 30605",
            "move_out_date": "2024-07-31",
            "total_withheld": 850.00
        }
    })
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
