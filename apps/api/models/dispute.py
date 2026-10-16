"""
Pydantic v2 schemas for Security Deposit Disputes and Statutory Demand Letters
Implements calculations under O.C.G.A. § 44-7-33, § 44-7-34, and § 44-7-35.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ConditionEvidenceItem(BaseModel):
    item_id: str
    area: str
    item_title: str
    withheld_amount: float
    wear_tear_classification: Literal["ORDINARY_WEAR_TEAR", "TENANT_DAMAGE"]
    statutory_assessment: str
    move_in_description: str
    move_out_description: str
    move_in_photo_url: Optional[str] = None
    move_out_photo_url: Optional[str] = None

class DisputeEvaluationRequest(BaseModel):
    tenant_name: str = "Alex M. Jordan"
    landlord_name: str = "Lakeside Student Commons LLC"
    property_address: str = "150 Riverbend Pkwy, Unit 304B, Athens, GA 30605"
    move_out_date: str = "2024-07-31" # YYYY-MM-DD
    inspection_list_date: Optional[str] = "2024-08-08" # 6 business days later (violates 3-day rule)
    deposit_returned_date: Optional[str] = None # None means not returned after 30+ days
    current_date: str = "2024-09-07" # 38 days after move-out
    monthly_rent: float = 1150.00
    deposit_paid: float = 2800.00
    total_withheld: float = 850.00
    items: List[ConditionEvidenceItem] = []

class DisputeEvaluationResponse(BaseModel):
    dispute_id: str
    inspection_business_days_elapsed: int
    inspection_timely: bool
    inspection_statute_citation: str
    return_calendar_days_elapsed: int
    return_timely: bool
    return_statute_citation: str
    forfeiture_triggered: bool
    forfeiture_reason: str
    treble_damages_eligible: bool
    treble_damages_amount: float
    total_potential_recovery: float
    summary_verdict: str
    move_out_date: str = ""
    inspection_list_date: Optional[str] = None
    deposit_returned_date: Optional[str] = None
    current_date: str = ""
    total_withheld: float = 0.0
    items_evaluated: List[ConditionEvidenceItem]

class DemandLetterRequest(BaseModel):
    evaluation: DisputeEvaluationRequest
    custom_notes: Optional[str] = None
