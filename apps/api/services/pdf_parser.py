"""
Coordinate-Preserving PDF Parser for LeaseGuard
Uses PyMuPDF to extract text blocks with exact [x0, y0, x1, y1] bounding boxes,
render high-resolution page preview images for the split-screen viewer,
and structure lease sections for grounding verification.
"""

import base64
import re
from typing import List, Tuple, Dict, Any, Optional
import pymupdf  # PyMuPDF
from apps.api.models.lease import BoundingBox, PageLayoutInfo, ParsedClauseBlock

class PDFParserService:
    def __init__(self, dpi: int = 150):
        self.dpi = dpi

    @staticmethod
    def _open(pdf_path: str):
        try:
            doc = pymupdf.open(pdf_path)
        except Exception as exc:
            raise ValueError(f"Could not open PDF: {exc}") from exc
        if doc.needs_pass:
            doc.close()
            raise ValueError("PDF is password protected")
        if len(doc) == 0:
            doc.close()
            raise ValueError("PDF has no pages")
        return doc

    def parse_lines(self, pdf_path: str) -> Dict[int, List[Tuple[str, List[float]]]]:
        """Per page: [(line_text, [x0, y0, x1, y1])] exactly as PyMuPDF lays the text out."""
        doc = self._open(pdf_path)
        out: Dict[int, List[Tuple[str, List[float]]]] = {}
        for idx in range(len(doc)):
            lines = []
            for block in doc[idx].get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block["lines"]:
                    text = "".join(span["text"] for span in line["spans"])
                    if text.strip():
                        lines.append((text, [round(v, 2) for v in line["bbox"]]))
            out[idx + 1] = lines
        doc.close()
        return out

    def parse_pdf(self, pdf_path: str) -> Tuple[List[PageLayoutInfo], List[ParsedClauseBlock], Dict[int, str]]:
        """
        Parses a PDF into:
        1. PageLayoutInfo list (with dimensions and base64 rendered page images)
        2. ParsedClauseBlock list with exact bounding box coordinates
        3. Full text per page dict {page_num: text} for substring verification
        """
        doc = self._open(pdf_path)
        pages_layout: List[PageLayoutInfo] = []
        clause_blocks: List[ParsedClauseBlock] = []
        page_full_texts: Dict[int, str] = {}

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]
            rect = page.rect
            width, height = float(rect.width), float(rect.height)

            # Render page image to high-res PNG for frontend canvas
            zoom = self.dpi / 72.0
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            img_b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

            pages_layout.append(
                PageLayoutInfo(
                    page_number=page_num,
                    width=width,
                    height=height,
                    image_base64=img_b64
                )
            )

            # Extract full text for exact substring grounding
            page_text = page.get_text("text")
            page_full_texts[page_num] = page_text

            # Extract blocks with coordinates
            # page.get_text("blocks") returns tuples: (x0, y0, x1, y1, text, block_no, block_type)
            blocks = page.get_text("blocks")
            current_section_title = None

            for b in blocks:
                # b[6] == 0 means text block (1 means image)
                if len(b) >= 7 and b[6] != 0:
                    continue

                x0, y0, x1, y1, raw_text = float(b[0]), float(b[1]), float(b[2]), float(b[3]), str(b[4]).strip()
                if not raw_text:
                    continue

                # Check if this block is a section header
                sec_match = re.search(r'(SECTION\s+\d+[\.:\sA-Z\-\[\]#]+)', raw_text, re.IGNORECASE)
                if sec_match:
                    current_section_title = sec_match.group(1).strip()
                    clause_id = f"PAGE_{page_num}_SEC_{len(clause_blocks) + 1}"
                else:
                    clause_id = f"PAGE_{page_num}_BLK_{len(clause_blocks) + 1}"

                # Ensure non-zero bounding box
                if x1 <= x0:
                    x1 = x0 + 10.0
                if y1 <= y0:
                    y1 = y0 + 10.0

                bbox = BoundingBox(
                    x0=round(x0, 2),
                    y0=round(y0, 2),
                    x1=round(x1, 2),
                    y1=round(y1, 2)
                )

                clause_blocks.append(
                    ParsedClauseBlock(
                        clause_id=clause_id,
                        page_number=page_num,
                        bounding_box=bbox,
                        text=raw_text,
                        section_title=current_section_title
                    )
                )

        doc.close()
        return pages_layout, clause_blocks, page_full_texts

    def find_text_bounding_box(self, pdf_path: str, search_text: str, page_number: int = 1) -> Optional[List[float]]:
        """
        Locates the exact bounding box [x0, y0, x1, y1] for a target search string on a specific page.
        """
        doc = self._open(pdf_path)
        if page_number > len(doc):
            doc.close()
            return None

        page = doc[page_number - 1]
        rects = page.search_for(search_text)
        doc.close()

        if rects:
            # Union of rects if multi-line
            x0 = min(r.x0 for r in rects)
            y0 = min(r.y0 for r in rects)
            x1 = max(r.x1 for r in rects)
            y1 = max(r.y1 for r in rects)
            return [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)]

        return None
