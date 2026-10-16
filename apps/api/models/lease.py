"""
Pydantic v2 structured schemas for LeaseGuard API
Enforces strict grounding and bounding-box validation under AGENTS.md rules.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator

class BoundingBox(BaseModel):
    x0: float = Field(..., description="Left coordinate in PDF points")
    y0: float = Field(..., description="Top coordinate in PDF points")
    x1: float = Field(..., description="Right coordinate in PDF points")
    y1: float = Field(..., description="Bottom coordinate in PDF points")

    @field_validator("x1")
    @classmethod
    def validate_x_bounds(cls, v: float, info) -> float:
        if "x0" in info.data and v < info.data["x0"]:
            raise ValueError("x1 must be greater than or equal to x0")
        return v

    @field_validator("y1")
    @classmethod
    def validate_y_bounds(cls, v: float, info) -> float:
        if "y0" in info.data and v < info.data["y0"]:
            raise ValueError("y1 must be greater than or equal to y0")
        return v

class PageLayoutInfo(BaseModel):
    page_number: int
    width: float
    height: float
    image_base64: Optional[str] = None

class ParsedClauseBlock(BaseModel):
    clause_id: str
    page_number: int
    bounding_box: BoundingBox
    text: str
    section_title: Optional[str] = None

class RetrievalScore(BaseModel):
    rule_id: str
    statute_section: str
    bm25_score: float
    vector_score: float
    rrf_score: float
    bm25_rank: Optional[int] = None
    vector_rank: Optional[int] = None

class FlaggedLeaseRisk(BaseModel):
    clause_id: str
    page_number: int
    bounding_box: List[float] = Field(..., min_length=4, max_length=4, description="[x0, y0, x1, y1] PDF coordinates")
    verbatim_lease_quote: str
    statute_citation: str
    rule_id: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    plain_english_explanation: str
    negotiation_counter_clause: str
    retrieval_telemetry: Optional[RetrievalScore] = None
    excess_amount: Optional[float] = None
    pii_redacted_clause_text: Optional[str] = None

class PIIRedactionLog(BaseModel):
    total_redacted: int
    entity_counts: Dict[str, int]
    redaction_latency_ms: float
    redacted_tokens: List[str]

class PipelineTelemetry(BaseModel):
    pdf_parse_ms: float
    pii_redaction_ms: float
    rule_eval_ms: float
    retrieval_ms: float
    total_ms: float
    pii_summary: PIIRedactionLog
    chunks_indexed: int
    statutes_evaluated: int
    storage_mode: str = "local_fallback"
    clauses_scanned: int = 0

class LeaseAuditResponse(BaseModel):
    lease_id: str
    filename: str
    property_address: str
    tenant_name_masked: str
    monthly_rent: Optional[float] = None
    security_deposit: Optional[float] = None
    deposit_cap_allowed: Optional[float] = None
    deposit_excess: float = 0.0
    overall_risk_score: int
    unenforceable_clauses_count: int
    flagged_risks: List[FlaggedLeaseRisk]
    pages: List[PageLayoutInfo]
    telemetry: PipelineTelemetry

class LeaseAnalyzeRequest(BaseModel):
    filename: Optional[str] = "athens_student_lease_sample.pdf"
    use_sample: bool = True
