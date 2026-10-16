"""
Deterministic Statutory Rules for LeaseGuard
Never relies on an LLM for numeric, cap, or deadline checks.
Executes exact Georgia statutory mathematics under O.C.G.A. §§ 44-7-13, 44-7-30.1, 44-7-33, 44-7-34, 44-7-35, and HB 404.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Tuple, Optional, Dict, List

WORD_NUMBERS = {
    "thirty": 30, "thirty-one": 31, "thirty-five": 35, "forty": 40, "forty-five": 45, "fifty": 50,
    "sixty": 60, "seventy": 70, "seventy-five": 75, "ninety": 90,
}
_MONEY = r"\$\s?([0-9][0-9,]*(?:\.[0-9]{2})?)"
_COOLING = r"(?:air[\s\-]*condition\w*|cooling|a/c|hvac)"


def _money(raw: str) -> float:
    return float(raw.replace(",", ""))


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.;!?])\s+(?=[A-Z(])", text) if s.strip()]


@dataclass
class RuleFinding:
    key: str                 # slug used in clause ids, e.g. DEPOSIT-CAP
    rule_id: str             # rule_id in georgia_statutes.json
    severity: str
    anchor: str              # regex locating the offending words on a single line of the clause
    explanation: str
    retrieval_query: str
    excess_amount: Optional[float] = None
    counter_params: Dict[str, str] = field(default_factory=dict)


class DeterministicStatutoryRules:
    @staticmethod
    def check_deposit_cap(monthly_rent: float, security_deposit: float) -> Tuple[bool, float, str]:
        """
        O.C.G.A. § 44-7-30.1 (Georgia Safe at Home Act / HB 404): deposit may not exceed 2 months' rent.
        Returns: (is_violation, excess_amount, statute_citation)
        """
        max_allowed = 2.0 * monthly_rent
        if security_deposit > max_allowed + 1e-9:
            return True, round(security_deposit - max_allowed, 2), "O.C.G.A. § 44-7-30.1"
        return False, 0.0, "O.C.G.A. § 44-7-30.1"

    @staticmethod
    def extract_monthly_rent(text: str) -> Optional[float]:
        flat = _flat(text)
        m = (re.search(r"monthly\s+(?:base\s+)?rent\s+of\s+[A-Za-z\s\-]*\(\s*" + _MONEY, flat, re.I)
             or re.search(r"monthly\s+(?:base\s+)?rent[^.$]{0,40}" + _MONEY, flat, re.I))
        return _money(m.group(1)) if m else None

    @staticmethod
    def extract_security_deposit(text: str) -> Optional[float]:
        """Amount the lease demands AS the security deposit (not amounts later deducted from it)."""
        for sent in _sentences(_flat(text)):
            if not re.search(r"security\s+deposit", sent, re.I):
                continue
            m = (re.search(_MONEY + r"\)?\s+as\s+(?:an?\s+|the\s+)?(?:[a-z\-]+\s+){0,3}(?:security\s+)?deposit", sent, re.I)
                 or re.search(r"security\s+deposit\s+(?:of|in\s+the\s+amount\s+of|totaling|equal\s+to)\s+[A-Za-z\s\-,]*\(?\s*" + _MONEY, sent, re.I))
            if m:
                return _money(m.group(1))
        return None

    @staticmethod
    def check_habitability_hvac(clause_text: str) -> Tuple[bool, str]:
        """
        O.C.G.A. § 44-7-13 & HB 404: duty to keep premises fit for habitation; cooling cannot be shifted or shut off.
        """
        t = _flat(clause_text).lower()
        shutoff = re.search(r"(?:shut\s*off|disable|discontinue|suspend|interrupt|disconnect|cut\s*off)\b[^.]{0,80}?" + _COOLING, t)
        deductible = re.search(r"deductible[^.]{0,80}?" + _COOLING + r"|" + _COOLING + r"[^.]{0,80}?deductible", t)
        tenant_pays = re.search(r"tenant[^.]{0,40}(?:responsible|pay|bear)[^.]{0,60}" + _COOLING + r"[^.]{0,40}(?:repair|maintenance|servicing)", t)
        as_is = "as-is" in t and re.search(_COOLING, t)
        return bool(shutoff or deductible or tenant_pays or as_is), "O.C.G.A. § 44-7-13 & HB 404"

    @staticmethod
    def check_cure_period(clause_text: str) -> Tuple[bool, str]:
        """
        HB 404 Safe at Home Act / O.C.G.A. § 44-7-50: mandatory 3-day written notice and right to cure.
        Flags notice waivers, immediate eviction filings, and zero-day cure windows.
        """
        t = _flat(clause_text).lower()
        waives = re.search(r"waives?\b[^.]{0,80}(?:notice|demand|grace|cure)", t)
        immediate = re.search(r"immediately\s+(?:file|institut\w*|commenc\w*)[^.]{0,80}(?:dispossessory|eviction)", t)
        no_notice = (re.search(r"without\s+(?:providing\s+)?(?:any\s+)?(?:preliminary\s+)?(?:\w+[\-\s]day\s+)?(?:written\s+)?(?:cure\s+)?notice", t)
                     and re.search(r"dispossessory|evict", t))
        return bool(waives or immediate or no_notice), "HB 404 Safe at Home Act (O.C.G.A. § 44-7-50)"

    @staticmethod
    def check_automatic_deduction(clause_text: str) -> Tuple[bool, str]:
        """
        O.C.G.A. § 44-7-33: deductions must be an itemised list of actual damage, never flat/automatic or for wear and tear.
        """
        t = _flat(clause_text).lower()
        if "deposit" not in t:
            return False, "O.C.G.A. § 44-7-33"
        automatic = re.search(r"automatically\s+deduct", t)
        flat = re.search(r"(?:non[\-\s]?refundable|flat)[^.]{0,60}(?:turnover|cleaning|carpet|paint)|(?:turnover|cleaning)\s+(?:charge|fee)", t)
        wear = re.search(r"regardless\s+of[^.]{0,120}wear\s+and\s+tear", t)
        return bool(automatic or flat or wear), "O.C.G.A. § 44-7-33"

    @staticmethod
    def check_refund_timeline_clause(clause_text: str) -> Tuple[bool, int, str]:
        """
        O.C.G.A. § 44-7-34: deposit must be returned within 30 calendar days. Flags any contractual period > 30.
        Only sentences that talk about returning the deposit are considered.
        """
        days = 0
        for sent in _sentences(_flat(clause_text)):
            low = sent.lower()
            if "deposit" not in low or not re.search(r"return|refund|deliver|remit|balance", low):
                continue
            nums = [int(n) for n in re.findall(r"(\d{1,3})\s*(?:calendar\s+|business\s+)?days", low)]
            nums += [v for w, v in WORD_NUMBERS.items() if re.search(rf"\b{w}\b\s*(?:\(\d+\)\s*)?(?:calendar\s+)?days", low)]
            if nums:
                days = max(nums)
                break
        return days > 30, days, "O.C.G.A. § 44-7-34"

    # ---- clause-level orchestration -------------------------------------------------
    def evaluate_clause(self, clause_text: str, monthly_rent: Optional[float]) -> List[RuleFinding]:
        flat = _flat(clause_text)
        out: List[RuleFinding] = []

        deposit = self.extract_security_deposit(flat)
        if deposit is not None and monthly_rent:
            violated, excess, _ = self.check_deposit_cap(monthly_rent, deposit)
            if violated:
                cap = 2.0 * monthly_rent
                out.append(RuleFinding(
                    key="DEPOSIT-CAP", rule_id="GA-HB404-DEPOSIT-CAP", severity="HIGH",
                    anchor=re.escape(f"{deposit:,.2f}"),
                    explanation=(f"Landlord charges a ${deposit:,.2f} security deposit on ${monthly_rent:,.2f} monthly rent. "
                                 f"Under O.C.G.A. § 44-7-30.1 (HB 404), residential deposits are capped at 2 months' rent "
                                 f"(${cap:,.2f}). The extra ${excess:,.2f} is unlawful and void."),
                    retrieval_query=f"security deposit cap two months rent HB 404 44-7-30.1 {flat}",
                    excess_amount=excess, counter_params={"MAX_DEPOSIT": f"{cap:,.2f}"}))

        if self.check_habitability_hvac(flat)[0]:
            out.append(RuleFinding(
                key="HVAC-HABITABILITY", rule_id="GA-HB404-HABITABILITY", severity="HIGH",
                anchor=r"deductible|shut off|disable|as-is|air conditioning",
                explanation=("Lease shifts air-conditioning costs to the tenant and/or lets the landlord disable cooling. Under "
                             "O.C.G.A. § 44-7-13 and the Georgia Safe at Home Act (HB 404), the landlord's duty to keep the premises "
                             "fit for habitation cannot be waived and cooling may not be shut off to coerce payment."),
                retrieval_query=f"HVAC air conditioning repair cooling shutoff habitability 44-7-13 HB 404 {flat}"))

        if self.check_cure_period(flat)[0]:
            out.append(RuleFinding(
                key="ZERO-NOTICE-EVICTION", rule_id="GA-HB404-CURE-PERIOD", severity="HIGH",
                anchor=r"cure notice|waives|notice to cure|without providing|immediately file",
                explanation=("The lease waives notice and the grace period and authorises an immediate eviction filing (0-day cure). "
                             "Georgia HB 404 requires a 3-day written notice and right to cure before any dispossessory filing; "
                             "a contractual waiver is void as against public policy."),
                retrieval_query=f"eviction 3-day right to cure notice dispossessory warrant HB 404 44-7-50 {flat}"))

        if self.check_automatic_deduction(flat)[0]:
            amt = re.search(_MONEY, flat)
            amount_txt = f"${_money(amt.group(1)):,.2f} " if amt else ""
            out.append(RuleFinding(
                key="AUTOMATIC-DEDUCTION", rule_id="GA-OCGA-44-7-33-INSPECTION", severity="HIGH",
                anchor=r"non-refundable|flat turnover|automatically|\$[\d,]+\.\d{2}",
                explanation=(f"Landlord imposes an automatic, non-refundable {amount_txt}turnover deduction regardless of move-in condition "
                             "or wear and tear. Under O.C.G.A. § 44-7-33, deposits cannot be docked for ordinary wear and tear and "
                             "any deduction must be an itemised list of actual damage compiled within 3 business days of surrender."),
                retrieval_query=f"damage list inspection deduction wear and tear 44-7-33 {flat}"))

        late, days, _ = self.check_refund_timeline_clause(flat)
        if late:
            out.append(RuleFinding(
                key="REFUND-TIMELINE", rule_id="GA-OCGA-44-7-34-RETURN", severity="HIGH",
                anchor=r"\(" + str(days) + r"\)|" + str(days) + r"\s+days",
                explanation=(f"Lease extends the deposit return window to {days} days. O.C.G.A. § 44-7-34 requires return within "
                             f"30 days, and a landlord who misses it forfeits the right to withhold and faces treble damages "
                             f"under § 44-7-35. Extending the deadline by contract is void."),
                retrieval_query=f"deposit refund return timeline 30 days treble damages 44-7-34 44-7-35 {flat}"))
        return out

    # ---- dates ------------------------------------------------------------------
    @staticmethod
    def compute_business_days(start_date: date, end_date: date) -> int:
        """Business days (Mon-Fri) elapsed after start_date up to and including end_date."""
        if start_date >= end_date:
            return 0
        business_days = 0
        curr = start_date + timedelta(days=1)
        while curr <= end_date:
            if curr.weekday() < 5:
                business_days += 1
            curr += timedelta(days=1)
        return business_days

    @classmethod
    def check_inspection_deadline(cls, move_out_str: str, inspection_str: Optional[str]) -> Tuple[bool, int, str]:
        """
        O.C.G.A. § 44-7-33: the damage list must be compiled within 3 business days of termination/surrender.
        Returns: (is_untimely_violation, business_days_elapsed, citation)
        """
        move_out = datetime.strptime(move_out_str, "%Y-%m-%d").date()
        if not inspection_str:
            return True, 999, "O.C.G.A. § 44-7-33"
        inspection = datetime.strptime(inspection_str, "%Y-%m-%d").date()
        biz_days = cls.compute_business_days(move_out, inspection)
        return biz_days > 3, biz_days, "O.C.G.A. § 44-7-33"

    @classmethod
    def check_return_deadline(cls, move_out_str: str, return_str: Optional[str], current_str: str) -> Tuple[bool, int, str]:
        """
        O.C.G.A. § 44-7-34 & § 44-7-35: deposit must be returned within 30 calendar days.
        Returns: (is_untimely_violation, calendar_days_elapsed, citation)
        """
        move_out = datetime.strptime(move_out_str, "%Y-%m-%d").date()
        ref_date = datetime.strptime(return_str, "%Y-%m-%d").date() if return_str else datetime.strptime(current_str, "%Y-%m-%d").date()
        days_elapsed = (ref_date - move_out).days
        return days_elapsed > 30, days_elapsed, "O.C.G.A. § 44-7-34 & § 44-7-35"
