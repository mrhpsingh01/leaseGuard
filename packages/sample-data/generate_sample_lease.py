"""
Programmatic Athens, GA Student Lease Generator
Generates a realistic 3-page off-campus student lease PDF near UGA containing 5 planted statutory violations:
1. $2,800 security deposit on $1,150 monthly rent (Violates O.C.G.A. § 44-7-30.1 deposit cap)
2. As-Is HVAC & Cooling Waiver with $500 tenant deductible and cooling shutoff authorization (Violates HB 404 & § 44-7-13)
3. Zero-Notice Eviction Filing waiving mandatory 3-day right-to-cure (Violates HB 404 & § 44-7-50)
4. Non-Refundable Carpet & Paint turnover deduction of $450 (Violates O.C.G.A. § 44-7-33)
5. 60-Day Deposit Refund Processing Window (Violates O.C.G.A. § 44-7-34 30-day deadline)
"""

import os
from pathlib import Path
import pymupdf  # PyMuPDF

_UNI_FONT = pymupdf.Font("helv")  # base-14 Helvetica as an embedded font so characters like the em dash survive


def _new_page(doc, width: float, height: float):
    """New page with a Unicode-capable Helvetica registered as "uni" (the base-14 'helv' mangles em dashes)."""
    page = doc.new_page(width=width, height=height)
    page.insert_font(fontname="uni", fontbuffer=_UNI_FONT.buffer)
    return page


def generate_athens_sample_lease(output_path: str = None) -> str:
    if output_path is None:
        base_dir = Path(__file__).parent
        output_path = str(base_dir / "athens_student_lease_sample.pdf")
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc = pymupdf.open()
    
    # Page dimensions: Standard Letter (612 x 792 points)
    page_width, page_height = 612.0, 792.0
    margin_x = 54.0  # 0.75 in
    content_width = page_width - (margin_x * 2)

    # -------------------------------------------------------------
    # PAGE 1: Parties, Property, Rent, and Section 3 (Violation 1)
    # -------------------------------------------------------------
    page1 = _new_page(doc, page_width, page_height)
    
    # Header Banner
    page1.draw_rect(pymupdf.Rect(margin_x, 35, page_width - margin_x, 75), color=(0.1, 0.2, 0.4), fill=(0.94, 0.96, 1.0), width=1)
    page1.insert_text(pymupdf.Point(margin_x + 14, 52), "LAKESIDE STUDENT COMMONS — RESIDENTIAL LEASE AGREEMENT", fontname="uni", fontsize=10.5)
    page1.insert_text(pymupdf.Point(margin_x + 14, 66), "Lakeside Student Commons — Athens, GA 30605  |  150 Riverbend Parkway, Clarke County, Georgia", fontname="uni", fontsize=8.5)

    y = 92.0

    # Intro Section
    page1.insert_text(pymupdf.Point(margin_x, y), "STATE OF GEORGIA, COUNTY OF CLARKE", fontname="uni", fontsize=9.5)
    y += 14
    intro_text = (
        "THIS RESIDENTIAL LEASE AGREEMENT ('Lease') is entered into as of August 1, 2024, by and between "
        "Lakeside Student Commons LLC ('Landlord'), and Tenant Alex M. Jordan ('Tenant'), Phone: (706) 555-0192, "
        "Email: alex.jordan@uga.edu, SSN: 123-45-6789. In consideration of the mutual covenants herein, the parties agree as follows:"
    )
    page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 45), intro_text, fontname="uni", fontsize=8.5)
    y += 48

    # Section 1: Leased Premises
    page1.insert_text(pymupdf.Point(margin_x, y), "SECTION 1. LEASED PREMISES", fontname="uni", fontsize=9.5)
    y += 14
    s1_body = "Landlord leases to Tenant, and Tenant leases from Landlord, Unit 304B located at 150 Riverbend Parkway, Athens, GA 30605 ('Premises'), for residential student housing purposes only."
    page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 30), s1_body, fontname="uni", fontsize=8.5)
    y += 34

    # Section 2: Term and Monthly Rent
    page1.insert_text(pymupdf.Point(margin_x, y), "SECTION 2. TERM AND MONTHLY RENT", fontname="uni", fontsize=9.5)
    y += 14
    s2_body = (
        "The term of this Lease shall commence on August 15, 2024, and terminate on July 31, 2025. "
        "Tenant covenants and agrees to pay Landlord monthly base rent of ONE THOUSAND ONE HUNDRED FIFTY DOLLARS ($1,150.00) "
        "due on the first (1st) day of each calendar month. Rent payments not received by 11:59 PM on the 5th day of the month shall incur a $75.00 late charge."
    )
    page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 55), s2_body, fontname="uni", fontsize=8.5)
    y += 60

    # Section 3: Security Deposit (VIOLATION 1)
    page1.insert_text(pymupdf.Point(margin_x, y), "SECTION 3. SECURITY DEPOSIT & UPFRONT CHARGES", fontname="uni", fontsize=9.5)
    y += 14
    s3_body = (
        "Upon execution of this Lease, Tenant shall deposit with Landlord the sum of TWO THOUSAND EIGHT HUNDRED DOLLARS ($2,800.00) "
        "as a mandatory security deposit to guarantee the faithful performance of all covenants herein. "
        "Tenant acknowledges that this security deposit equals approximately 2.43 months' rent and agrees that such sum is necessary to secure against student tenant default."
    )
    page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 60), s3_body, fontname="uni", fontsize=8.5)
    y += 66

    # Section 4: Utilities and Services
    page1.insert_text(pymupdf.Point(margin_x, y), "SECTION 4. UTILITIES AND INTERNET", fontname="uni", fontsize=9.5)
    y += 14
    s4_body = "Water and municipal trash collection shall be billed as a flat utility fee of $45.00 per month. Tenant shall establish an individual electricity account with Georgia Power and high-speed internet service in Tenant's own name prior to move-in."
    page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 40), s4_body, fontname="uni", fontsize=8.5)
    y += 46

    # Section 5: Occupancy and Guests
    page1.insert_text(pymupdf.Point(margin_x, y), "SECTION 5. OCCUPANCY LIMITS AND GUESTS", fontname="uni", fontsize=9.5)
    y += 14
    s5_body = "The Premises shall be occupied solely by Alex M. Jordan. Overnight guests are permitted for no more than three (3) consecutive nights and no more than seven (7) total nights in any calendar month without prior written consent."
    page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 40), s5_body, fontname="uni", fontsize=8.5)
    y += 46

    # Section 6: Rules and Parking
    page1.insert_text(pymupdf.Point(margin_x, y), "SECTION 6. PARKING AND COMMUNITY REGULATIONS", fontname="uni", fontsize=9.5)
    y += 14
    s6_body = "One designated resident parking permit is included. Vehicles parked without a valid Lakeside sticker or parked in fire lanes shall be towed at the vehicle owner's sole expense. Quiet hours are enforced Sunday through Thursday from 10:00 PM to 8:00 AM."
    page1.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 45), s6_body, fontname="uni", fontsize=8.5)

    page1.insert_text(pymupdf.Point(page_width / 2 - 25, page_height - 25), "Page 1 of 3", fontname="uni", fontsize=8)

    # -------------------------------------------------------------
    # PAGE 2: Sections 7 (Violation 2), 8, 9 (Violation 3), 10, 11
    # -------------------------------------------------------------
    page2 = _new_page(doc, page_width, page_height)
    y = 45.0

    page2.insert_text(pymupdf.Point(margin_x, y), "LAKESIDE STUDENT COMMONS — RESIDENTIAL LEASE AGREEMENT (CONT.)", fontname="uni", fontsize=9.5)
    y += 24

    # Section 7: As-Is HVAC & Cooling Waiver (VIOLATION 2)
    page2.insert_text(pymupdf.Point(margin_x, y), "SECTION 7. AS-IS HVAC & COOLING WAIVER", fontname="uni", fontsize=9.5)
    y += 14
    s7_body = (
        "Tenant agrees to accept the heating, ventilation, and air conditioning (HVAC) systems in AS-IS condition. "
        "Tenant shall be responsible for paying the first $500.00 deductible for all air conditioning maintenance, compressor repairs, and seasonal servicing. "
        "Furthermore, if any monthly rent payment is delinquent by more than five (5) days, Landlord reserves the absolute right to shut off or disable "
        "air conditioning and cooling services to the unit until all outstanding balances and late fees are settled in full."
    )
    page2.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 80), s7_body, fontname="uni", fontsize=8.5)
    y += 88

    # Section 8: Routine Tenant Maintenance
    page2.insert_text(pymupdf.Point(margin_x, y), "SECTION 8. ROUTINE TENANT UPKEEP AND SMOKE DETECTORS", fontname="uni", fontsize=9.5)
    y += 14
    s8_body = "Tenant shall keep the unit clean, dispose of household trash in designated dumpsters, and replace smoke detector batteries as required. Tenant shall promptly notify management in writing of any water leaks, dripping faucets, or mold growth."
    page2.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 45), s8_body, fontname="uni", fontsize=8.5)
    y += 52

    # Section 9: Default and Zero-Notice Eviction (VIOLATION 3)
    page2.insert_text(pymupdf.Point(margin_x, y), "SECTION 9. DEFAULT & ZERO-NOTICE EVICTION FILING", fontname="uni", fontsize=9.5)
    y += 14
    s9_body = (
        "In the event Tenant fails to remit full rent or fees when due, Tenant expressly waives all rights to any demand, statutory grace period, "
        "or notice to cure. Landlord may immediately file an affidavit for a dispossessory warrant and eviction proceeding in Clarke County Magistrate Court "
        "without providing any preliminary three-day written cure notice, any provision of Georgia statutory law notwithstanding."
    )
    page2.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 70), s9_body, fontname="uni", fontsize=8.5)
    y += 78

    # Section 10: Subleasing and Roommates
    page2.insert_text(pymupdf.Point(margin_x, y), "SECTION 10. SUBLETTING AND ASSIGNMENT", fontname="uni", fontsize=9.5)
    y += 14
    s10_body = "Tenant may sublease or assign the Premises during UGA summer semester only upon Landlord's written approval, passing credit screening, and payment of a $150.00 administrative assignment fee."
    page2.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 40), s10_body, fontname="uni", fontsize=8.5)
    y += 48

    # Section 11: Landlord Entry and Inspection
    page2.insert_text(pymupdf.Point(margin_x, y), "SECTION 11. LANDLORD ACCESS AND RIGHT OF INSPECTION", fontname="uni", fontsize=9.5)
    y += 14
    s11_body = "Landlord or Landlord's authorized agents may enter the Premises during reasonable business hours with twenty-four (24) hours advance notice for inspections, maintenance, or showing prospective tenants, or immediately without notice in emergencies."
    page2.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 45), s11_body, fontname="uni", fontsize=8.5)

    page2.insert_text(pymupdf.Point(page_width / 2 - 25, page_height - 25), "Page 2 of 3", fontname="uni", fontsize=8)

    # -------------------------------------------------------------
    # PAGE 3: Sections 12, 13, 14 (Violation 4), 15, 16 (Violation 5), Signatures
    # -------------------------------------------------------------
    page3 = _new_page(doc, page_width, page_height)
    y = 45.0

    page3.insert_text(pymupdf.Point(margin_x, y), "LAKESIDE STUDENT COMMONS — RESIDENTIAL LEASE AGREEMENT (CONT.)", fontname="uni", fontsize=9.5)
    y += 24

    # Section 12: Surrender of Premises
    page3.insert_text(pymupdf.Point(margin_x, y), "SECTION 12. SURRENDER OF PREMISES AND KEY RETURN", fontname="uni", fontsize=9.5)
    y += 14
    s12_body = "At the conclusion of the lease term, Tenant shall vacate the premises, remove all personal property, and return all electronic key fobs and mailbox keys to the management office before 12:00 PM on July 31, 2025."
    page3.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 40), s12_body, fontname="uni", fontsize=8.5)
    y += 48

    # Section 13: Move-In Condition Statement
    page3.insert_text(pymupdf.Point(margin_x, y), "SECTION 13. MOVE-IN INSPECTION CHECKLIST", fontname="uni", fontsize=9.5)
    y += 14
    s13_body = "A move-in comprehensive condition checklist signed by both parties shall serve as the official baseline for preexisting damages to the Premises."
    page3.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 35), s13_body, fontname="uni", fontsize=8.5)
    y += 42

    # Section 14: Automatic Carpet & Paint Deduction (VIOLATION 4)
    page3.insert_text(pymupdf.Point(margin_x, y), "SECTION 14. AUTOMATIC CARPET & PAINT DEDUCTION", fontname="uni", fontsize=9.5)
    y += 14
    s14_body = (
        "Upon vacancy, Landlord shall automatically deduct a non-refundable flat turnover charge of FOUR HUNDRED FIFTY DOLLARS ($450.00) "
        "from Tenant's security deposit for routine wall repainting, ozone treatment, and commercial carpet steam cleaning, regardless of the move-in condition, "
        "actual cleaning status, or normal wear and tear of the premises."
    )
    page3.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 70), s14_body, fontname="uni", fontsize=8.5)
    y += 78

    # Section 15: Governing Law & Jurisdiction
    page3.insert_text(pymupdf.Point(margin_x, y), "SECTION 15. SEVERABILITY AND VENUE", fontname="uni", fontsize=9.5)
    y += 14
    s15_body = "This agreement is governed by the laws of the State of Georgia. Any legal actions or proceedings arising hereunder shall be brought solely in the Magistrate or Superior Court of Clarke County, Georgia."
    page3.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 35), s15_body, fontname="uni", fontsize=8.5)
    y += 44

    # Section 16: Security Deposit Return Timeline (VIOLATION 5)
    page3.insert_text(pymupdf.Point(margin_x, y), "SECTION 16. DEPOSIT REFUND TIMELINE & PROCESSING", fontname="uni", fontsize=9.5)
    y += 14
    s16_body = (
        "Landlord shall inspect the premises and deliver any remaining balance of the security deposit, together with an accounting, "
        "within sixty (60) days following complete physical surrender of the premises and receipt of Tenant's forwarding address in writing. "
        "Tenant acknowledges that student turnover peaks require up to 60 days to finalize contractor invoicing."
    )
    page3.insert_textbox(pymupdf.Rect(margin_x, y, margin_x + content_width, y + 70), s16_body, fontname="uni", fontsize=8.5)
    y += 82

    # Signature Block
    page3.draw_line(pymupdf.Point(margin_x, y), pymupdf.Point(page_width - margin_x, y), color=(0.7, 0.7, 0.7), width=1)
    y += 16
    page3.insert_text(pymupdf.Point(margin_x, y), "IN WITNESS WHEREOF, the parties hereto have executed this Lease Agreement as of August 1, 2024.", fontname="uni", fontsize=8.5)
    y += 26

    # Landlord signature column
    page3.insert_text(pymupdf.Point(margin_x, y), "LANDLORD: Lakeside Student Commons LLC", fontname="uni", fontsize=8.5)
    page3.insert_text(pymupdf.Point(margin_x, y + 14), "By: /s/ Marcus Vance, Property Manager", fontname="uni", fontsize=8.5)
    page3.insert_text(pymupdf.Point(margin_x, y + 26), "Date: August 1, 2024", fontname="uni", fontsize=7.5)

    # Tenant signature column
    col2_x = margin_x + 260
    page3.insert_text(pymupdf.Point(col2_x, y), "TENANT: Alex M. Jordan (UGA '25)", fontname="uni", fontsize=8.5)
    page3.insert_text(pymupdf.Point(col2_x, y + 14), "Signature: /s/ Alex M. Jordan", fontname="uni", fontsize=8.5)
    page3.insert_text(pymupdf.Point(col2_x, y + 26), "Date: August 1, 2024", fontname="uni", fontsize=7.5)

    page3.insert_text(pymupdf.Point(page_width / 2 - 25, page_height - 25), "Page 3 of 3", fontname="uni", fontsize=8)

    doc.save(output_path)
    doc.close()
    print(f"[OK] Generated sample Athens student lease: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_athens_sample_lease()
