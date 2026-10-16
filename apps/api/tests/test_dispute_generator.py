"""
Tests for Security Deposit Dispute and Demand Letter Generator
"""

import os
import pymupdf
from apps.api.models.dispute import DisputeEvaluationRequest, DemandLetterRequest
from apps.api.services.dispute_generator import DisputeGeneratorService

def test_dispute_evaluation_timelines():
    service = DisputeGeneratorService()
    
    # 2024-07-31 (Wednesday) to 2024-08-07 (Wednesday) is 5 business days
    req = DisputeEvaluationRequest(
        move_out_date="2024-07-31",
        inspection_list_date="2024-08-07",
        current_date="2024-09-10",
        total_withheld=850.00
    )

    resp = service.evaluate_dispute(req)
    assert resp.inspection_business_days_elapsed == 5
    assert resp.inspection_timely is False, "5 business days exceeds statutory 3-day window"
    assert resp.return_calendar_days_elapsed == 41
    assert resp.return_timely is False, "41 days exceeds 30-day statutory window"
    assert resp.forfeiture_triggered is True
    assert resp.treble_damages_eligible is True
    assert resp.treble_damages_amount == 2550.00
    assert resp.total_potential_recovery == 2550.00
    assert len(resp.items_evaluated) == 2

def test_demand_letter_pdf_generation(tmp_path):
    service = DisputeGeneratorService()
    out_pdf = str(tmp_path / "test_demand_letter.pdf")

    demand_req = DemandLetterRequest(
        evaluation=DisputeEvaluationRequest(
            tenant_name="Alex M. Jordan",
            landlord_name="Lakeside Student Commons LLC",
            property_address="150 Riverbend Pkwy, Unit 304B, Athens, GA 30605",
            total_withheld=850.00
        )
    )

    res_path = service.generate_demand_letter_pdf(demand_req, output_path=out_pdf)
    assert os.path.exists(res_path)
    assert os.path.getsize(res_path) > 1000

    doc = pymupdf.open(res_path)
    assert len(doc) >= 1
    page1_text = doc[0].get_text()
    assert "FORMAL STATUTORY DEMAND" in page1_text
    assert "Alex M. Jordan" in page1_text
    assert "Lakeside Student Commons LLC" in page1_text
    assert "O.C.G.A. § 44-7-35" in page1_text
    assert "$2,550.00" in page1_text or "$850.00" in page1_text
    doc.close()
