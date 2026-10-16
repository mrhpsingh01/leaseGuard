"""
Security Deposit Dispute Routes for LeaseGuard
Provides statutory dispute evaluation, sample scenarios, and downloadable demand letter PDFs.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from apps.api.models.dispute import (
    DisputeEvaluationRequest,
    DisputeEvaluationResponse,
    DemandLetterRequest
)
from apps.api.services.dispute_generator import DisputeGeneratorService

router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])
generator = DisputeGeneratorService()

@router.get("/sample-scenario", response_model=DisputeEvaluationRequest)
async def get_sample_dispute_scenario():
    """Returns the default Athens off-campus deposit dispute scenario."""
    return DisputeEvaluationRequest()

@router.post("/evaluate", response_model=DisputeEvaluationResponse)
async def evaluate_dispute(req: DisputeEvaluationRequest):
    """Evaluates statutory compliance under O.C.G.A. § 44-7-33, § 44-7-34, and § 44-7-35."""
    return generator.evaluate_dispute(req)

@router.post("/demand-letter")
async def generate_demand_letter(req: DemandLetterRequest):
    """Generates and returns an attorney-grade legal demand letter PDF."""
    pdf_path = generator.generate_demand_letter_pdf(req)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate demand letter PDF")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="Security_Deposit_Demand_Letter_OCGA_44-7-35.pdf",
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(os.unlink, pdf_path),  # temp file removed after the response is sent
    )
