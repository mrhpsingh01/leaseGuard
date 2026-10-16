"""
Tests for Coordinate-Preserving PDF Parser
"""

import os
from pathlib import Path
from apps.api.services.pdf_parser import PDFParserService
from apps.api.config import SAMPLE_LEASE_PATH

def test_pdf_parser_page_layout():
    parser = PDFParserService(dpi=100)
    assert os.path.exists(SAMPLE_LEASE_PATH), "Sample lease PDF must exist"

    layouts, clause_blocks, page_texts = parser.parse_pdf(str(SAMPLE_LEASE_PATH))
    assert len(layouts) == 3
    for layout in layouts:
        assert layout.width > 500
        assert layout.height > 700
        assert layout.image_base64.startswith("data:image/png;base64,")

    assert len(clause_blocks) > 10, "Should have extracted multiple clause blocks"

    # Verify bounding boxes are within page bounds
    for block in clause_blocks:
        bbox = block.bounding_box
        assert 0 <= bbox.x0 < bbox.x1 <= 612.0
        assert 0 <= bbox.y0 < bbox.y1 <= 792.0

def test_find_text_bounding_box():
    parser = PDFParserService()
    # Search for $2,800.00 on Page 1
    bbox = parser.find_text_bounding_box(str(SAMPLE_LEASE_PATH), "$2,800.00", page_number=1)
    assert bbox is not None
    assert len(bbox) == 4
    x0, y0, x1, y1 = bbox
    assert x1 > x0 and y1 > y0

    # Search for HVAC on Page 2
    bbox2 = parser.find_text_bounding_box(str(SAMPLE_LEASE_PATH), "AS-IS", page_number=2)
    assert bbox2 is not None
