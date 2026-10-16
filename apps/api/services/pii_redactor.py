"""
Local Regex/NER PII Redactor for LeaseGuard
Scans and redacts tenant names, phone numbers, emails, SSNs, and bank account numbers
prior to any downstream LLM/retrieval call, logs telemetry, and provides deterministic local re-hydration.
Nothing here touches the network.
"""

import re
import time
from typing import Dict, Tuple, List
from apps.api.models.lease import PIIRedactionLog

_NAME_TOKEN = r"(?:[A-Z][a-z]+|[A-Z]\.)"
_NAME_STOPWORDS = {"Lease", "Agreement", "Premises", "Phone", "Email", "Signature", "Date", "Landlord", "Tenant",
                   "Agrees", "Shall", "Hereby", "Residential", "Property", "Unit", "Address", "SSN"}
CATEGORIES = ("TENANT_NAME", "EMAIL", "PHONE", "SSN", "ACCOUNT")


class PIIRedactorService:
    def __init__(self):
        self.ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        self.phone_pattern = re.compile(r"(?<![\w$])(?:\+?1[-. ]?)?(?:\(\d{3}\)\s?|\d{3}[-. ])\d{3}[-. ]\d{4}\b")
        self.account_pattern = re.compile(r"\b(?:Acct|Account|Routing)(?:\s*(?:No\.?|Number))?\s*#?:?\s*(\d{8,17})\b", re.IGNORECASE)
        # "Tenant Alex M. Jordan", "Tenant: Jane Doe", "Resident - Sam Lee" (case-sensitive so only Capitalised words match)
        self.name_context_pattern = re.compile(
            rf"\b(?:Tenant|TENANT|Lessee|Resident|Occupant)s?\b\s*[:\-]?\s+({_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{1,3}})")
        self.hydration_map: Dict[str, str] = {}
        self.counter: Dict[str, int] = {c: 0 for c in CATEGORIES}

    def reset(self) -> None:
        self.hydration_map.clear()
        self.counter = {c: 0 for c in CATEGORIES}

    def _placeholder(self, category: str, original: str) -> str:
        for ph, val in self.hydration_map.items():
            if val == original and ph.startswith(f"[{category}_"):
                return ph
        self.counter[category] += 1
        ph = f"[{category}_{self.counter[category]}]"
        self.hydration_map[ph] = original
        return ph

    @staticmethod
    def _clean_name(raw: str) -> str:
        parts = raw.split()
        while parts and parts[-1] in _NAME_STOPWORDS:
            parts.pop()
        return " ".join(parts)

    def redact(self, text: str) -> Tuple[str, PIIRedactionLog]:
        """Redact one document. Placeholder numbering restarts for each call."""
        start = time.perf_counter()
        self.reset()
        redacted = text

        redacted = self.ssn_pattern.sub(lambda m: self._placeholder("SSN", m.group(0)), redacted)
        redacted = self.email_pattern.sub(lambda m: self._placeholder("EMAIL", m.group(0)), redacted)
        redacted = self.phone_pattern.sub(lambda m: self._placeholder("PHONE", m.group(0)), redacted)

        def _acct(m: "re.Match[str]") -> str:
            ph = self._placeholder("ACCOUNT", m.group(1))
            return m.group(0)[: m.start(1) - m.start(0)] + ph
        redacted = self.account_pattern.sub(_acct, redacted)

        # Learn tenant names from context, then mask every occurrence of each learned name (longest first).
        names = {self._clean_name(m.group(1)) for m in self.name_context_pattern.finditer(redacted)}
        for name in sorted((n for n in names if len(n.split()) >= 2), key=len, reverse=True):
            ph = self._placeholder("TENANT_NAME", name)
            redacted = re.sub(rf"(?<![\w\[]){re.escape(name)}(?!\w)", ph, redacted)

        counts = {c: sum(1 for ph in self.hydration_map if ph.startswith(f"[{c}_")) for c in CATEGORIES}
        log = PIIRedactionLog(
            total_redacted=sum(counts.values()),
            entity_counts=counts,
            redaction_latency_ms=round((time.perf_counter() - start) * 1000.0, 3),
            redacted_tokens=list(self.hydration_map.keys()),
        )
        return redacted, log

    def mask_known(self, text: str) -> str:
        """Mask any already-discovered PII values in derived text (e.g. a clause or retrieval query)."""
        out = text
        for ph, original in sorted(self.hydration_map.items(), key=lambda kv: len(kv[1]), reverse=True):
            out = out.replace(original, ph)
        return out

    def rehydrate(self, redacted_text: str) -> str:
        """Restore original values from the local hydration map (never leaves this process)."""
        result = redacted_text
        for placeholder, original in self.hydration_map.items():
            result = result.replace(placeholder, original)
        return result
