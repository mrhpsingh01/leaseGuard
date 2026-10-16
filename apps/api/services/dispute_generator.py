"""
Security Deposit Dispute and Statutory Demand Letter Generator for LeaseGuard
Calculates timeline compliance, forfeiture under O.C.G.A. § 44-7-33 / § 44-7-34,
and treble damages under O.C.G.A. § 44-7-35, generating formal printable legal demand letters via PyMuPDF.
"""

import os
import tempfile
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Tuple, List, Optional
import pymupdf  # PyMuPDF

_UNI_FONT = pymupdf.Font("helv")  # base-14 Helvetica as an embedded font so characters like the em dash survive


def _new_page(doc, width: float, height: float):
    """New page with a Unicode-capable Helvetica registered as "uni" (the base-14 'helv' mangles em dashes)."""
    page = doc.new_page(width=width, height=height)
    page.insert_font(fontname="uni", fontbuffer=_UNI_FONT.buffer)
    return page

from apps.api.models.dispute import (
    DisputeEvaluationRequest,
    DisputeEvaluationResponse,
    ConditionEvidenceItem,
    DemandLetterRequest
)
from apps.api.services.deterministic_rules import DeterministicStatutoryRules

class DisputeGeneratorService:
    def __init__(self):
        self.rules = DeterministicStatutoryRules()

    def evaluate_dispute(self, req: DisputeEvaluationRequest) -> DisputeEvaluationResponse:
        # 1. Inspection compliance
        is_insp_violation, insp_biz_days, insp_citation = self.rules.check_inspection_deadline(
            req.move_out_date,
            req.inspection_list_date
        )

        # 2. Return compliance
        is_ret_violation, ret_cal_days, ret_citation = self.rules.check_return_deadline(
            req.move_out_date,
            req.deposit_returned_date,
            req.current_date
        )

        forfeiture_triggered = is_insp_violation or is_ret_violation

        # Build forfeiture reason
        reasons = []
        if is_insp_violation:
            reasons.append(f"Move-out inspection list provided after {insp_biz_days} business days (statutory limit is 3 business days under {insp_citation})")
        if is_ret_violation:
            reasons.append(f"Security deposit not returned after {ret_cal_days} calendar days (statutory limit is 30 calendar days under {ret_citation})")

        forfeiture_reason = "; ".join(reasons) if reasons else "No statutory timeline forfeiture detected."

        # Treble damages calculation under O.C.G.A. § 44-7-35
        # Landlord liable for 3x sum improperly withheld
        treble_damages_eligible = forfeiture_triggered and req.total_withheld > 0
        treble_amount = round(req.total_withheld * 3.0, 2) if treble_damages_eligible else 0.0
        total_recovery = treble_amount if treble_damages_eligible else req.total_withheld

        summary_verdict = (
            f"FORFEITURE TRIGGERED: Landlord forfeited all legal rights to retain any portion of the "
            f"${req.total_withheld:,.2f} security deposit withholding under O.C.G.A. § 44-7-35. "
            f"Tenant is entitled to immediate full refund plus treble damages of ${treble_amount:,.2f}."
            if forfeiture_triggered else
            "Inspection and return complied with statutory deadlines. Review individual condition deductions."
        )

        # Default sample evidence items if empty
        items = req.items
        if not items:
            items = [
                ConditionEvidenceItem(
                    item_id="ITEM-1",
                    area="Living Room & Walls",
                    item_title="Wall Scuff Touch-Up & Paint",
                    withheld_amount=400.00,
                    wear_tear_classification="ORDINARY_WEAR_TEAR",
                    statutory_assessment="Faded paint and minor pinhole nail marks constitute ordinary wear and tear under Georgia law, which cannot be lawfully deducted.",
                    move_in_description="Minor scuffs on baseboard noted at move-in.",
                    move_out_description="Standard picture hanging nail holes and furniture rub marks.",
                    move_in_photo_url="/sample-photos/living_room_move_in.svg",
                    move_out_photo_url="/sample-photos/living_room_move_out.svg"
                ),
                ConditionEvidenceItem(
                    item_id="ITEM-2",
                    area="Bedrooms & Hallway",
                    item_title="Commercial Carpet Steam Cleaning",
                    withheld_amount=450.00,
                    wear_tear_classification="ORDINARY_WEAR_TEAR",
                    statutory_assessment="Flat non-negotiable turnover carpet cleaning deduction violates O.C.G.A. § 44-7-33.",
                    move_in_description="Carpet showed light traffic shading.",
                    move_out_description="Normal student foot traffic; vacuumed clean with no pet or water stains.",
                    move_in_photo_url="/sample-photos/carpet_move_in.svg",
                    move_out_photo_url="/sample-photos/carpet_move_out.svg"
                )
            ]

        return DisputeEvaluationResponse(
            dispute_id=str(uuid.uuid4()),
            inspection_business_days_elapsed=insp_biz_days,
            inspection_timely=not is_insp_violation,
            inspection_statute_citation=insp_citation,
            return_calendar_days_elapsed=ret_cal_days,
            return_timely=not is_ret_violation,
            return_statute_citation=ret_citation,
            forfeiture_triggered=forfeiture_triggered,
            forfeiture_reason=forfeiture_reason,
            treble_damages_eligible=treble_damages_eligible,
            treble_damages_amount=treble_amount,
            total_potential_recovery=total_recovery,
            summary_verdict=summary_verdict,
            move_out_date=req.move_out_date,
            inspection_list_date=req.inspection_list_date,
            deposit_returned_date=req.deposit_returned_date,
            current_date=req.current_date,
            total_withheld=req.total_withheld,
            items_evaluated=items
        )

    def generate_demand_letter_pdf(self, req: DemandLetterRequest, output_path: Optional[str] = None) -> str:
        """
        Generates a formal, attorney-grade legal demand letter PDF using PyMuPDF.
        """
        eval_resp = self.evaluate_dispute(req.evaluation)
        ev = req.evaluation

        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".pdf", prefix="demand_letter_")
            os.close(fd)

        doc = pymupdf.open()
        page_width, page_height = 612.0, 792.0
        margin_x = 54.0
        content_width = page_width - (margin_x * 2)

        # ---------------- PAGE 1 ----------------
        page1 = _new_page(doc, page_width, page_height)
        y = 50.0

        # Title / Formal Header
        page1.insert_text(pymupdf.Point(margin_x, y), "FORMAL STATUTORY DEMAND FOR RETURN OF SECURITY DEPOSIT", fontname="uni", fontsize=11)
        y += 14
        page1.insert_text(pymupdf.Point(margin_x, y), "DELIVERED VIA CERTIFIED MAIL & ELECTRONIC TRANSMISSION", fontname="uni", fontsize=8.5)
        y += 18
        page1.draw_line(pymupdf.Point(margin_x, y), pymupdf.Point(page_width - margin_x, y), color=(0.2, 0.2, 0.2), width=1)
        y += 24

        # Date & Addressee
        today_str = datetime.now().strftime("%B %d, %Y")
        page1.insert_text(pymupdf.Point(margin_x, y), f"Date: {today_str}", fontname="uni", fontsize=9)
        y += 16
        page1.insert_text(pymupdf.Point(margin_x, y), f"TO: {ev.landlord_name}", fontname="uni", fontsize=9)
        y += 14
        page1.insert_text(pymupdf.Point(margin_x, y), f"Property Management & Legal Notice Department", fontname="uni", fontsize=8.5)
        y += 14
        page1.insert_text(pymupdf.Point(margin_x, y), f"{ev.property_address}", fontname="uni", fontsize=8.5)
        y += 22

        # Subject Line
        re_text = f"RE: MANDATORY RETURN OF SECURITY DEPOSIT UNDER O.C.G.A. §§ 44-7-33, 44-7-34, & 44-7-35 | UNIT: {ev.property_address}"
        page1.draw_rect(pymupdf.Rect(margin_x, y - 4, page_width - margin_x, y + 20), color=(0.85, 0.85, 0.85), fill=(0.95, 0.95, 0.95))
        page1.insert_text(pymupdf.Point(margin_x + 8, y + 12), re_text, fontname="uni", fontsize=8.5)
        y += 36

        # Body Paragraphs
        p1 = (
            f"Dear Management of {ev.landlord_name}:\n\n"
            f"This letter serves as formal legal notice on behalf of Tenant {ev.tenant_name} regarding the residential lease for "
            f"the premises located at {ev.property_address}. Tenant vacated the premises and surrendered complete possession on {ev.move_out_date}, "
            f"having paid an upfront security deposit of ${ev.deposit_paid:,.2f}.\n\n"
            f"To date, Landlord has unlawfully retained ${ev.total_withheld:,.2f} of Tenant's deposit. Notice is hereby given that Landlord's "
            f"withholding is completely void and forfeited as a matter of Georgia statutory law due to the following non-curable statutory violations:"
        )
        page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 100), p1, fontname="uni", fontsize=8.5)
        y += 105

        # Violation Points Box
        vbox_y = y
        page1.draw_rect(pymupdf.Rect(margin_x, vbox_y, margin_x + content_width, vbox_y + 160), color=(0.8, 0.2, 0.2), fill=(1.0, 0.97, 0.97), width=1)
        
        vy = vbox_y + 16
        page1.insert_text(pymupdf.Point(margin_x + 12, vy), "1. FORFEITURE UNDER O.C.G.A. § 44-7-33 (UNTIMELY MOVE-OUT INSPECTION):", fontname="uni", fontsize=8.5)
        vy += 14
        v1_desc = (
            f"Under Georgia law, landlords must compile a comprehensive written list of damages within three (3) business days of surrender. "
            f"Landlord failed to provide an inspection list until {eval_resp.inspection_business_days_elapsed} business days after vacancy. Under § 44-7-35, "
            f"failure to strictly comply with § 44-7-33 forfeits all rights to withhold any portion of the security deposit."
        )
        page1.insert_textbox(pymupdf.Rect(margin_x + 12, vy, margin_x + content_width - 12, vy + 40), v1_desc, fontname="uni", fontsize=8)
        
        vy += 46
        page1.insert_text(pymupdf.Point(margin_x + 12, vy), "2. FORFEITURE UNDER O.C.G.A. § 44-7-34 (MISSED 30-DAY STATUTORY DEADLINE):", fontname="uni", fontsize=8.5)
        vy += 14
        v2_desc = (
            f"O.C.G.A. § 44-7-34 mandates full refund of the security deposit within 30 calendar days of vacancy. "
            f"{eval_resp.return_calendar_days_elapsed} calendar days have elapsed without lawful return. Failure to return within 30 days constitutes an "
            f"automatic forfeiture of any right to retain deposit funds."
        )
        page1.insert_textbox(pymupdf.Rect(margin_x + 12, vy, margin_x + content_width - 12, vy + 40), v2_desc, fontname="uni", fontsize=8)

        y = vbox_y + 175

        # Statutory Treble Damages Warning
        p2 = (
            f"STATUTORY DEMAND AND TREBLE DAMAGES NOTICE PURSUANT TO O.C.G.A. § 44-7-35:\n\n"
            f"Under O.C.G.A. § 44-7-35(c), any landlord who wrongfully or in bad faith withholds a tenant's security deposit shall be liable in an "
            f"amount equal to THREE TIMES THE SUM IMPROPERLY WITHHELD (${eval_resp.treble_damages_amount:,.2f}), plus reasonable attorney's fees "
            f"and court filing costs in the Magistrate Court of Athens-Clarke County, Georgia."
        )
        page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 70), p2, fontname="uni", fontsize=8.5)
        y += 75

        # Deadline and Demand
        demand_text = (
            f"Tenant hereby demands delivery of a cashier's check or electronic transfer in the amount of ${ev.total_withheld:,.2f} "
            f"within ten (10) calendar days of receipt of this notice. If full payment is not received within 10 days, Tenant will immediately file "
            f"a civil statement of claim in Athens-Clarke County Magistrate Court demanding the full statutory treble damage award of "
            f"${eval_resp.treble_damages_amount:,.2f} plus statutory attorney's fees."
        )
        page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 55), demand_text, fontname="uni", fontsize=8.5)
        y += 65

        # Sign-off
        page1.insert_text(pymupdf.Point(margin_x, y), "Respectfully submitted,", fontname="uni", fontsize=9)
        y += 24
        page1.insert_text(pymupdf.Point(margin_x, y), f"/s/ {ev.tenant_name}", fontname="uni", fontsize=9.5)
        y += 14
        page1.insert_text(pymupdf.Point(margin_x, y), f"Tenant — {ev.property_address}", fontname="uni", fontsize=8.5)
        y += 14
        page1.insert_text(pymupdf.Point(margin_x, y), "Cc: Athens-Clarke County Tenant Union; Tenant Records File", fontname="uni", fontsize=8)

        page1.insert_text(pymupdf.Point(page_width / 2 - 25, page_height - 25), "Page 1 of 1", fontname="uni", fontsize=8)

        doc.save(output_path)
        doc.close()
        return output_path
