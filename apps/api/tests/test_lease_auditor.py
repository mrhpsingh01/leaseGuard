"""
Tests for Lease Auditor Service
Verifies 100% detection of planted violations, coordinate validity, and substring grounding.
"""

import os
import pymupdf
from apps.api.services.lease_auditor import LeaseAuditorService
from apps.api.config import SAMPLE_LEASE_PATH

def test_lease_auditor_planted_violations():
    auditor = LeaseAuditorService()
    assert os.path.exists(SAMPLE_LEASE_PATH)

    audit = auditor.audit_lease(str(SAMPLE_LEASE_PATH))

    # Basic validations
    assert audit.monthly_rent == 1150.00
    assert audit.security_deposit == 2800.00
    assert audit.deposit_cap_allowed == 2300.00
    assert audit.deposit_excess == 500.00
    assert audit.overall_risk_score == 100
    assert audit.unenforceable_clauses_count == 5

    # Check that all 5 planted violations are caught
    rule_ids = [r.rule_id for r in audit.flagged_risks]
    assert "GA-HB404-DEPOSIT-CAP" in rule_ids
    assert "GA-HB404-HABITABILITY" in rule_ids
    assert "GA-HB404-CURE-PERIOD" in rule_ids
    assert "GA-OCGA-44-7-33-INSPECTION" in rule_ids
    assert "GA-OCGA-44-7-34-RETURN" in rule_ids

    # Grounding check: verify that verbatim quote is an exact substring of the PDF page text
    doc = pymupdf.open(str(SAMPLE_LEASE_PATH))
    for risk in audit.flagged_risks:
        page_text = doc[risk.page_number - 1].get_text()
        assert risk.verbatim_lease_quote in page_text, f"Verbatim quote must exist on page {risk.page_number}"
        # Bounding box bounds check
        bbox = risk.bounding_box
        assert len(bbox) == 4
        assert bbox[0] < bbox[2]
        assert bbox[1] < bbox[3]
    doc.close()

    # Telemetry checks
    assert audit.telemetry.total_ms > 0
    assert audit.telemetry.pii_summary.total_redacted >= 4
    assert audit.telemetry.chunks_indexed == 5
