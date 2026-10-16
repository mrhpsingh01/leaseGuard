"""
Lease Auditor Service for LeaseGuard
Real pipeline (nothing hardcoded to the sample lease):

  1. PyMuPDF layout + line-level bounding boxes
  2. Local PII redaction (names, phones, emails, SSNs, accounts) before any retrieval/LLM-facing text is built
  3. Deterministic statutory rules (deposit cap math, cooling/habitability, cure-period, deductions, refund window)
  4. Hybrid RAG (BM25 + cosine vector + Reciprocal Rank Fusion) grounding every finding in the statute corpus
  5. Strict grounding: verbatim_lease_quote is an exact substring of the page text; bbox is the quoted line's box

`pipeline()` is a generator that yields SSE-ready events as each stage / clause completes.
"""

import os
import re
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional, Tuple

from apps.api.models.lease import (
    FlaggedLeaseRisk,
    LeaseAuditResponse,
    PipelineTelemetry,
)
from apps.api.services.deterministic_rules import DeterministicStatutoryRules, RuleFinding
from apps.api.services.hybrid_retriever import HybridRetrieverService
from apps.api.services.pdf_parser import PDFParserService
from apps.api.services.pii_redactor import PIIRedactorService

SEVERITY_WEIGHT = {"HIGH": 20, "MEDIUM": 10, "LOW": 5}
_STREET = r"(?:Parkway|Pkwy|Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir)"


def page_lines_text(lines: List[Tuple[str, List[float]]]) -> str:
    return "\n".join(t for t, _ in lines)


class LeaseAuditorService:
    def __init__(self, statutes_path: Optional[str] = None, retriever: Optional[HybridRetrieverService] = None):
        self.parser = PDFParserService(dpi=150)
        self.rules = DeterministicStatutoryRules()
        self.retriever = retriever or HybridRetrieverService(statutes_path=statutes_path)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _extract_address(text: str) -> str:
        flat = re.sub(r"\s+", " ", text)
        street = re.search(rf"\b(\d{{1,6}}\s+[A-Z][A-Za-z0-9.]*(?:\s+[A-Z][A-Za-z0-9.]*){{0,3}}\s+{_STREET})\b", flat)
        if not street:
            return "Address not detected"
        parts = [street.group(1)]
        unit = re.search(r"\bUnit\s+([A-Za-z0-9\-]+)", flat)
        if unit:
            parts.append(f"Unit {unit.group(1)}")
        city = re.search(r"\b([A-Z][a-z]+),?\s+(?:GA|Georgia)\s+(\d{5})\b", flat)
        if city:
            parts.append(f"{city.group(1)}, GA {city.group(2)}")
        return ", ".join(parts)

    @staticmethod
    def _lines_in_block(page_lines: List[Tuple[str, List[float]]], bbox: List[float]) -> List[Tuple[str, List[float]]]:
        x0, y0, x1, y1 = bbox
        out = []
        for text, lb in page_lines:
            cx, cy = (lb[0] + lb[2]) / 2.0, (lb[1] + lb[3]) / 2.0
            if x0 - 1 <= cx <= x1 + 1 and y0 - 1 <= cy <= y1 + 1:
                out.append((text, lb))
        return out

    @staticmethod
    def _pick_quote(block_lines: List[Tuple[str, List[float]]], anchor: str) -> Optional[Tuple[str, List[float]]]:
        """Choose the single layout line holding the anchor, trimmed to the sentence fragment around it."""
        if not block_lines:
            return None
        pattern = re.compile(anchor, re.IGNORECASE)
        for text, lb in block_lines:
            m = pattern.search(text)
            if m:
                left = max(text.rfind(". ", 0, m.start()) + 2, 0) if text.rfind(". ", 0, m.start()) != -1 else 0
                right = text.find(". ", m.end())
                fragment = text[left: right + 1 if right != -1 else len(text)].strip()
                return (fragment if len(fragment) >= 12 else text.strip()), lb
        return block_lines[0][0].strip(), block_lines[0][1]

    # ---------------------------------------------------------------- pipeline
    def pipeline(self, pdf_path: str, filename: Optional[str] = None) -> Iterator[Tuple[str, Any]]:
        """Yields ("progress", dict) | ("clause", FlaggedLeaseRisk) | ("complete", LeaseAuditResponse)."""
        total_start = time.perf_counter()
        filename = filename or os.path.basename(pdf_path)

        # 1. PDF layout
        t0 = time.perf_counter()
        pages_layout, clause_blocks, page_texts = self.parser.parse_pdf(pdf_path)
        page_lines = self.parser.parse_lines(pdf_path)
        parse_ms = (time.perf_counter() - t0) * 1000.0
        combined_text = "\n".join(page_texts[p] for p in sorted(page_texts))
        if not combined_text.strip():
            raise ValueError("PDF contains no selectable text (scanned PDFs need OCR)")
        yield "progress", {"stage": "PARSING_PDF", "elapsed_ms": round(parse_ms, 2),
                           "message": f"PyMuPDF extracted {len(clause_blocks)} text blocks with bounding boxes from {len(pages_layout)} pages"}

        # 2. Local PII redaction
        t0 = time.perf_counter()
        redactor = PIIRedactorService()
        _, pii_log = redactor.redact(combined_text)
        pii_ms = (time.perf_counter() - t0) * 1000.0
        tenant_masked = next((ph for ph in pii_log.redacted_tokens if ph.startswith("[TENANT_NAME_")), "[NOT_DETECTED]")
        yield "progress", {"stage": "PII_REDACTION", "elapsed_ms": round(pii_ms, 2),
                           "message": f"Masked {pii_log.total_redacted} PII entities locally before retrieval"}

        # 3 + 4. Deterministic rules and hybrid retrieval, clause by clause
        rent = self.rules.extract_monthly_rent(combined_text)
        deposit = self.rules.extract_security_deposit(combined_text)
        cap_allowed = 2.0 * rent if rent else None
        yield "progress", {"stage": "DETERMINISTIC_RULES",
                           "message": "Evaluating Georgia HB 404 & O.C.G.A. statutory rules" +
                                      (f" (rent ${rent:,.2f}, deposit ${deposit:,.2f})" if rent and deposit else "")}

        rule_ms = 0.0
        retrieval_ms = 0.0
        risks: List[FlaggedLeaseRisk] = []
        used_ids: set = set()
        statutes_by_id = {s["rule_id"]: s for s in self.retriever.statutes}
        pages_by_num = {p.page_number: p for p in pages_layout}

        for idx, block in enumerate(clause_blocks):
            if re.match(r"^\s*SECTION\s+\d+[^\n]*$", block.text.strip(), re.IGNORECASE) and "\n" not in block.text.strip():
                continue  # bare section header
            t0 = time.perf_counter()
            findings: List[RuleFinding] = self.rules.evaluate_clause(block.text, rent)
            rule_ms += (time.perf_counter() - t0) * 1000.0

            for f in findings:
                statute = statutes_by_id.get(f.rule_id)
                if statute is None:
                    continue
                picked = self._pick_quote(self._lines_in_block(page_lines[block.page_number],
                                                               [block.bounding_box.x0, block.bounding_box.y0,
                                                                block.bounding_box.x1, block.bounding_box.y1]), f.anchor)
                if picked is None:
                    continue
                quote, bbox = picked
                page = pages_by_num[block.page_number]
                # Grounding guards: exact substring + in-bounds box
                if quote not in page_texts[block.page_number]:
                    continue
                if quote != "" and quote in page_lines_text(page_lines[block.page_number]):
                    tight = self.parser.find_text_bounding_box(pdf_path, quote, block.page_number)
                    if tight:
                        bbox = tight
                x0, y0, x1, y1 = bbox
                bbox = [max(0.0, x0), max(0.0, y0), min(page.width, x1), min(page.height, y1)]
                if not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
                    continue

                t0 = time.perf_counter()
                ranked = self.retriever.retrieve(redactor.mask_known(f.retrieval_query), top_k=len(statutes_by_id))
                retrieval_ms += (time.perf_counter() - t0) * 1000.0
                score = next(sc for st, sc in ranked if st["rule_id"] == f.rule_id)

                sec = re.search(r"SECTION\s+(\d+)", block.section_title or "", re.IGNORECASE)
                clause_id = f"SEC-{sec.group(1)}-{f.key}" if sec else f"P{block.page_number}-B{idx}-{f.key}"
                while clause_id in used_ids:
                    clause_id += "-X"
                used_ids.add(clause_id)

                counter = statute["standard_counter_clause"]
                for k, v in f.counter_params.items():
                    counter = counter.replace(f"[{k}]", v)

                risk = FlaggedLeaseRisk(
                    clause_id=clause_id, page_number=block.page_number, bounding_box=[round(v, 2) for v in bbox],
                    verbatim_lease_quote=quote, statute_citation=statute["statute_title"], rule_id=f.rule_id,
                    severity=f.severity, plain_english_explanation=f.explanation, negotiation_counter_clause=counter,
                    retrieval_telemetry=score, excess_amount=f.excess_amount,
                    pii_redacted_clause_text=redactor.mask_known(re.sub(r"\s+", " ", block.text).strip()),
                )
                risks.append(risk)
                yield "clause", risk

        total_ms = (time.perf_counter() - total_start) * 1000.0
        telemetry = PipelineTelemetry(
            pdf_parse_ms=round(parse_ms, 2), pii_redaction_ms=round(pii_ms, 3), rule_eval_ms=round(max(rule_ms, 0.001), 3),
            retrieval_ms=round(retrieval_ms, 2), total_ms=round(total_ms, 2), pii_summary=pii_log,
            chunks_indexed=len(self.retriever.corpus_texts), statutes_evaluated=len(statutes_by_id),
            storage_mode=self.retriever.storage_mode, clauses_scanned=len(clause_blocks),
        )
        result = LeaseAuditResponse(
            lease_id=str(uuid.uuid4()), filename=filename, property_address=self._extract_address(combined_text),
            tenant_name_masked=tenant_masked, monthly_rent=rent, security_deposit=deposit, deposit_cap_allowed=cap_allowed,
            deposit_excess=round(deposit - cap_allowed, 2) if (deposit and cap_allowed and deposit > cap_allowed) else 0.0,
            overall_risk_score=min(100, sum(SEVERITY_WEIGHT[r.severity] for r in risks)),
            unenforceable_clauses_count=len(risks), flagged_risks=risks, pages=pages_layout, telemetry=telemetry,
        )
        yield "complete", result

    def audit_lease(self, pdf_path: str, filename: Optional[str] = None) -> LeaseAuditResponse:
        result: Optional[LeaseAuditResponse] = None
        for kind, payload in self.pipeline(pdf_path, filename):
            if kind == "complete":
                result = payload
        assert result is not None
        return result
