"""
Tests for Athens Sample Lease Generator
"""

import os
import importlib.util
from pathlib import Path
import pymupdf

def get_sample_lease_module():
    base_dir = Path(__file__).resolve().parents[3]
    script_path = base_dir / "packages" / "sample-data" / "generate_sample_lease.py"
    spec = importlib.util.spec_from_file_location("generate_sample_lease", str(script_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_sample_lease_generation(tmp_path):
    mod = get_sample_lease_module()
    test_pdf = str(tmp_path / "test_lease.pdf")
    generated_path = mod.generate_athens_sample_lease(test_pdf)
    assert os.path.exists(generated_path)

    doc = pymupdf.open(generated_path)
    assert len(doc) == 3, "Lease must have exactly 3 pages"

    # Verify Page 1 has Section 3 ($2,800 deposit)
    p1_text = doc[0].get_text()
    assert "$1,150.00" in p1_text
    assert "$2,800.00" in p1_text
    assert "SECTION 3" in p1_text

    # Verify Page 2 has Section 7 (HVAC waiver) and Section 9 (Zero-notice eviction)
    p2_text = doc[1].get_text()
    assert "AS-IS HVAC & COOLING WAIVER" in p2_text or "HVAC" in p2_text
    assert "$500.00 deductible" in p2_text
    assert "shut off or disable" in p2_text
    assert "SECTION 9" in p2_text
    assert "without providing any preliminary three-day written cure notice" in p2_text

    # Verify Page 3 has Section 14 (Automatic carpet deduction) and Section 16 (60-day refund)
    p3_text = doc[2].get_text()
    assert "AUTOMATIC CARPET & PAINT DEDUCTION" in p3_text
    assert "$450.00" in p3_text
    assert "SECTION 16" in p3_text
    assert "sixty (60) days" in p3_text

    doc.close()
