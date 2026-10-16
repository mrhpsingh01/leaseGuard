"""
Production-readiness suite: runs against the real sample PDF and the real FastAPI app (no mocks).
"""

import json
import subprocess
import sys
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from apps.api.config import SAMPLE_LEASE_PATH
from apps.api.main import app
from apps.api.services.lease_auditor import LeaseAuditorService
from apps.api.services.pii_redactor import PIIRedactorService
from apps.api.services.statute_store import StatuteStore

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "packages" / "sample-data" / "generate_sample_lease.py"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs lifespan (store + index init)
        yield c


@pytest.fixture(scope="module")
def audit():
    return LeaseAuditorService().audit_lease(str(SAMPLE_LEASE_PATH))


def parse_sse(body: str):
    events = []
    for chunk in body.strip().split("\n\n"):
        lines = chunk.split("\n")
        name = next(l[7:] for l in lines if l.startswith("event: "))
        data = json.loads(next(l[6:] for l in lines if l.startswith("data: ")))
        events.append((name, data))
    return events


def make_lease(path: Path, rent: str, rent_words: str, dep: str, dep_words: str, refund_days: str) -> str:
    """Tiny single-page lease with caller-chosen numbers, to prove the auditor is not hardcoded to the sample."""
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    body = (
        "SECTION 1. RENT\n"
        f"Tenant agrees to pay monthly base rent of {rent_words} DOLLARS (${rent}) on the first of each month.\n\n"
        "SECTION 2. SECURITY DEPOSIT\n"
        f"Tenant shall deposit with Landlord the sum of {dep_words} DOLLARS (${dep}) as a security deposit.\n\n"
        "SECTION 3. RETURN OF DEPOSIT\n"
        f"Landlord shall return the balance of the security deposit within {refund_days} days after surrender of the premises.\n\n"
        "SECTION 4. PARKING\nOne parking permit is included. Quiet hours begin at 10 PM.\n"
    )
    page.insert_textbox(pymupdf.Rect(54, 54, 558, 500), body, fontname="helv", fontsize=10)
    doc.save(str(path))
    doc.close()
    return str(path)


# ---------------------------------------------------------------- Gate 2 table
def test_sample_pdf_generation():
    subprocess.run([sys.executable, str(GENERATOR)], check=True, capture_output=True, cwd=str(REPO_ROOT))
    pdf = REPO_ROOT / "packages" / "sample-data" / "athens_student_lease_sample.pdf"
    assert pdf.exists() and pdf.stat().st_size > 0
    doc = pymupdf.open(str(pdf))
    assert len(doc) == 3
    assert "Lakeside Student Commons — Athens, GA 30605" in doc[0].get_text()
    doc.close()


EXPECTED = {
    "GA-HB404-DEPOSIT-CAP": "44-7-30.1",
    "GA-HB404-HABITABILITY": "HB 404",
    "GA-HB404-CURE-PERIOD": "HB 404",
    "GA-OCGA-44-7-33-INSPECTION": "44-7-33",
    "GA-OCGA-44-7-34-RETURN": "44-7-34",
}


def test_all_5_georgia_violations_caught(audit):
    assert len(audit.flagged_risks) == 5, [r.clause_id for r in audit.flagged_risks]
    by_rule = {r.rule_id: r for r in audit.flagged_risks}
    assert set(by_rule) == set(EXPECTED)
    for rule_id, needle in EXPECTED.items():
        assert needle in by_rule[rule_id].statute_citation
        assert by_rule[rule_id].severity == "HIGH"
        assert by_rule[rule_id].negotiation_counter_clause.strip()
    dep = by_rule["GA-HB404-DEPOSIT-CAP"]
    assert (audit.monthly_rent, audit.security_deposit, audit.deposit_cap_allowed) == (1150.0, 2800.0, 2300.0)
    assert dep.excess_amount == 500.0 and "2,300.00" in dep.negotiation_counter_clause
    assert "air conditioning" in by_rule["GA-HB404-HABITABILITY"].verbatim_lease_quote
    assert "450" in by_rule["GA-OCGA-44-7-33-INSPECTION"].plain_english_explanation
    assert "sixty (60) days" in by_rule["GA-OCGA-44-7-34-RETURN"].verbatim_lease_quote
    assert "60 days" in by_rule["GA-OCGA-44-7-34-RETURN"].plain_english_explanation
    # every finding carries both hybrid retrieval signals
    for r in audit.flagged_risks:
        t = r.retrieval_telemetry
        assert t.bm25_score > 0 and t.vector_score > 0 and t.rrf_score > 0


def test_zero_hallucinated_quotes_and_bboxes(audit, client):
    doc = pymupdf.open(str(SAMPLE_LEASE_PATH))
    checked = 0
    for r in audit.flagged_risks:
        page = doc[r.page_number - 1]
        x0, y0, x1, y1 = r.bounding_box
        assert r.verbatim_lease_quote in page.get_text("text")
        assert 0 <= x0 < x1 <= page.rect.width and 0 <= y0 < y1 <= page.rect.height
        # the box really encloses the quoted words (not just any in-bounds rectangle)
        inside = " ".join(page.get_textbox(pymupdf.Rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1)).split())
        assert " ".join(r.verbatim_lease_quote.split()[:4]) in inside
        checked += 1
    assert checked == 5
    # same guarantee over the streaming endpoint
    events = parse_sse(client.get("/api/v1/leases/analyze-stream").text)
    clauses = [d for n, d in events if n == "clause_analyzed"]
    assert len(clauses) == 5
    for c in clauses:
        page = doc[c["page_number"] - 1]
        bx0, by0, bx1, by1 = c["bounding_box"]
        assert c["verbatim_lease_quote"] in page.get_text("text")
        assert 0 <= bx0 < bx1 <= page.rect.width and 0 <= by0 < by1 <= page.rect.height
    doc.close()


def test_pii_redaction_roundtrip():
    snippet = ("Tenant Alex M. Jordan can be reached at (706) 555-0199 or alex.jordan@uga.edu. "
               "SSN on file: 123-45-6789. Rent is $1,150.00.")
    r = PIIRedactorService()
    out, log = r.redact(snippet)
    for placeholder in ("[TENANT_NAME_1]", "[PHONE_1]", "[EMAIL_1]", "[SSN_1]"):
        assert placeholder in out
    for raw in ("Alex M. Jordan", "(706) 555-0199", "alex.jordan@uga.edu", "123-45-6789"):
        assert raw not in out
    assert "$1,150.00" in out  # non-PII is untouched
    assert log.total_redacted == 4
    assert r.rehydrate(out) == snippet


def test_dispute_timeline_and_pdf_export(client):
    scenario = {
        "tenant_name": "Alex M. Jordan",
        "landlord_name": "Lakeside Student Commons LLC",
        "property_address": "150 Riverbend Parkway, Unit 304B, Athens, GA 30605",
        "move_out_date": "2024-07-31",          # Wednesday
        "inspection_list_date": "2024-08-08",   # 6 business days later
        "deposit_returned_date": None,
        "current_date": "2024-09-07",           # 38 calendar days after move-out
        "monthly_rent": 1150.0, "deposit_paid": 2800.0, "total_withheld": 850.0,
    }
    ev = client.post("/api/v1/disputes/evaluate", json=scenario)
    assert ev.status_code == 200
    body = ev.json()
    assert body["inspection_business_days_elapsed"] == 6 and body["inspection_timely"] is False
    assert "44-7-33" in body["inspection_statute_citation"]
    assert body["return_calendar_days_elapsed"] == 38 and body["return_timely"] is False
    assert "44-7-34" in body["return_statute_citation"]
    assert body["forfeiture_triggered"] is True and body["treble_damages_eligible"] is True
    assert body["treble_damages_amount"] == 2550.0  # 3 x $850 under 44-7-35
    assert "44-7-35" in body["summary_verdict"]

    pdf = client.post("/api/v1/disputes/demand-letter", json={"evaluation": scenario})
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF-") and len(pdf.content) > 2048
    doc = pymupdf.open(stream=pdf.content, filetype="pdf")
    text = " ".join(doc[0].get_text().split())
    assert all(s in text for s in ("44-7-33", "44-7-34", "44-7-35", "$2,550.00", "6 business days", "38 calendar days"))


# ---------------------------------------------------------------- beyond the table
def test_auditor_is_not_hardcoded_to_the_sample(tmp_path):
    a = LeaseAuditorService()
    clean = a.audit_lease(make_lease(tmp_path / "ok.pdf", "1,000.00", "ONE THOUSAND", "1,800.00", "ONE THOUSAND EIGHT HUNDRED", "thirty (30)"))
    assert clean.flagged_risks == [] and clean.overall_risk_score == 0
    bad = a.audit_lease(make_lease(tmp_path / "bad.pdf", "900.00", "NINE HUNDRED", "2,000.00", "TWO THOUSAND", "forty-five (45)"))
    rules = {r.rule_id: r for r in bad.flagged_risks}
    assert set(rules) == {"GA-HB404-DEPOSIT-CAP", "GA-OCGA-44-7-34-RETURN"}
    assert rules["GA-HB404-DEPOSIT-CAP"].excess_amount == 200.0
    assert bad.deposit_cap_allowed == 1800.0


def test_health_and_zero_config_fallback(client, tmp_path):
    h = client.get("/api/v1/health").json()
    assert h == {"status": "ok", "statutes_loaded": 5, "sample_pdf_ready": True, "storage_mode": "local_fallback"}
    # unreachable Postgres must degrade gracefully, never crash cold start
    store = StatuteStore(database_url="postgresql://nobody:nopw@127.0.0.1:1/none", sqlite_path=str(tmp_path / "s.db"))
    assert store.mode == "local_fallback" and len(store.statutes) == 5 and store.pg_error
    assert (tmp_path / "s.db").exists()


def test_sse_headers_and_event_order(client):
    r = client.get("/api/v1/leases/analyze-stream")
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache, no-transform"
    assert r.headers["x-accel-buffering"] == "no"
    assert r.headers["connection"] == "keep-alive"
    events = parse_sse(r.text)
    names = [n for n, _ in events]
    assert names[-1] == "complete" and names.count("clause_analyzed") == 5
    stages = {d.get("stage") for n, d in events if n == "progress"}
    assert {"PARSING_PDF", "PII_REDACTION", "DETERMINISTIC_RULES"} <= stages


def test_upload_and_rejection(client):
    with open(SAMPLE_LEASE_PATH, "rb") as f:
        r = client.post("/api/v1/leases/analyze-stream", files={"file": ("my_lease.pdf", f, "application/pdf")})
    complete = [d for n, d in parse_sse(r.text) if n == "complete"][0]
    assert complete["filename"] == "my_lease.pdf" and len(complete["flagged_risks"]) == 5
    bad = client.post("/api/v1/leases/analyze-stream", files={"file": ("x.pdf", b"not a pdf", "application/pdf")})
    assert bad.status_code == 415


def test_cors_allows_vercel_and_localhost_only(client):
    def preflight(origin):
        return client.options("/api/v1/health", headers={"Origin": origin, "Access-Control-Request-Method": "GET"})
    assert preflight("http://localhost:3000").headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert preflight("https://leaseguard-demo.vercel.app").headers.get("access-control-allow-origin") == "https://leaseguard-demo.vercel.app"
    assert "access-control-allow-origin" not in preflight("https://evil.example.com").headers
