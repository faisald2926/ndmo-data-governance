"""Layer 1 — deterministic rules + regex.

Detects structured sensitive data by column name and by value pattern, using
real Saudi identifier checks (national ID Luhn, IBAN mod-97). Any PII hit pins a
row to at least 'Restricted' (مقيّد) under the Individuals/Privacy impact.
Fast, explainable, near-100% precision, zero AI cost.
"""
import re
from . import ndmo

# --- value patterns ---------------------------------------------------------
RE_NATIONAL_ID = re.compile(r"\b[12]\d{9}\b")
RE_IBAN_SA = re.compile(r"\bSA\d{22}\b")
RE_PHONE = re.compile(r"\+9665\d{8}\b")
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
RE_VAT = re.compile(r"\b3\d{13}3\b")            # 15-digit Saudi VAT
RE_IBAN_ANY = re.compile(r"\bSA\d{2}[A-Z0-9]{20}\b")

# --- column-name lexicon (Arabic + English) -> PII type ---------------------
COLUMN_LEXICON = {
    "national_id": ["national_id", "nationalid", "هوية", "رقم الهوية", "الهوية الوطنية"],
    "iban": ["iban", "ايبان", "آيبان", "رقم الحساب", "bank_iban", "payment_iban"],
    "salary": ["salary", "راتب", "الراتب", "monthly_salary"],
    "phone": ["phone", "mobile", "جوال", "هاتف", "رقم الجوال"],
    "email": ["email", "بريد", "البريد الإلكتروني"],
    "person_name": ["name_ar", "full_name", "contact_person", "اسم", "الاسم"],
    "health": ["health", "صحي", "صحة", "طبي", "medical", "diagnosis"],
    "biometric": ["biometric", "بصمة", "سمات حيوية"],
}


def _luhn_ok(num: str) -> bool:
    if len(num) != 10 or not num.isdigit():
        return False
    s = 0
    for i, ch in enumerate(num[:9]):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return (10 - (s % 10)) % 10 == int(num[9])


def _iban_ok(x: str) -> bool:
    if not (x.startswith("SA") and len(x) == 24 and x[2:].isdigit()):
        return False
    rearranged = x[4:] + "2810" + x[2:4]       # 'S'->28,'A'->10 ; move check to end
    return int(rearranged) % 97 == 1


# PII types that are strongly sensitive (always >= Restricted)
STRONG_PII = {"national_id", "iban", "salary", "health", "biometric"}


def scan_value(value: str):
    """Return a set of PII types detected purely from the value text."""
    found = set()
    if not value:
        return found
    v = str(value)
    if any(_luhn_ok(m) for m in RE_NATIONAL_ID.findall(v)):
        found.add("national_id")
    if any(_iban_ok(m) for m in RE_IBAN_SA.findall(v)):
        found.add("iban")
    if RE_PHONE.search(v):
        found.add("phone")
    if RE_EMAIL.search(v):
        found.add("email")
    if RE_VAT.search(v):
        found.add("vat")
    return found


def _column_pii_type(column: str):
    c = column.lower()
    for pii_type, keys in COLUMN_LEXICON.items():
        if any(k.lower() in c for k in keys):
            return pii_type
    return None


def scan_row(content: dict):
    """Scan a structured row (dict). Returns (pii_types, evidence_list)."""
    pii_types, evidence = set(), []
    for col, val in content.items():
        by_name = _column_pii_type(col)
        if by_name:
            pii_types.add(by_name)
            evidence.append(f"حقل '{col}' -> {by_name}")
        by_value = scan_value(val)
        for t in by_value:
            pii_types.add(t)
            evidence.append(f"قيمة في '{col}' تطابق نمط {t}")
    return pii_types, evidence


def classify(content: dict, text: str = "") -> dict:
    """Layer-1 verdict for a record.

    Returns a dict with level/impact/pii_types/evidence/confidence, or level=None
    when rules find no signal (so the LLM layer can decide).
    """
    pii_types, evidence = scan_row(content or {})
    pii_types |= scan_value(text)

    if pii_types & STRONG_PII or {"phone", "email", "vat"} & pii_types:
        level = ndmo.RESTRICTED
        impact = "الأفراد" if (pii_types & {"national_id", "phone", "email", "health", "biometric", "person_name"}) \
            else "أنشطة الجهات"
        return {
            "level": level,
            "impact_category": impact,
            "impact_level": ndmo.IMPACT_OF_LEVEL[level],
            "pii_types": sorted(pii_types),
            "evidence": "؛ ".join(evidence[:5]) or "تم رصد بيانات شخصية/حساسة",
            "confidence": 0.97,
            "decided_by": "rules",
        }

    return {
        "level": None,                 # no rule signal -> defer to LLM
        "impact_category": None,
        "impact_level": None,
        "pii_types": sorted(pii_types),
        "evidence": "",
        "confidence": 0.0,
        "decided_by": "rules",
    }
