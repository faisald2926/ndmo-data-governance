"""NDMO Data-Quality engine — the 6 dimensions.

Completeness · Uniqueness · Timeliness · Validity · Accuracy · Consistency.
Each dimension is a rule with a metric and an escalation threshold. Returns
per-row findings (comparable to data/quality_issues_log.csv) and a scorecard.
"""
import datetime as dt

import pandas as pd

from classification.rules import _iban_ok, _luhn_ok

TODAY = dt.date(2026, 6, 21)
VAT_RATE = 0.15

# id column used to report row_id per source file
ID_COL = {
    "01_vendors_master.csv": "vendor_id",
    "02_invoices.csv": "invoice_no",
    "03_employees_payroll.csv": "employee_id",
    "04_citizen_service_requests.csv": "request_id",
    "05_documents_register.csv": "doc_id",
    "06_open_datasets.csv": "record_id",
}

# Per-file rule configuration
RULES = {
    "01_vendors_master.csv": {
        "required": ["contact_email", "contact_phone"],
        "unique": "cr_number",
        "timeliness": ("last_updated", 365 * 3),
        "iban_cols": ["iban"],
        "vat_cols": ["vat_number"],
        "consistency": {"status": ["نشط"]},
    },
    "02_invoices.csv": {
        "required": ["cost_center"],
        "unique": "invoice_no",
        "iban_cols": ["payment_iban"],
        "national_id_cols": ["approved_by_id"],
        "non_negative": ["subtotal", "total_amount"],
        "no_future": ["issue_date"],
        "accuracy_vat": ("subtotal", "vat_amount", "total_amount"),
        "consistency": {"currency": ["SAR"]},
    },
    "03_employees_payroll.csv": {
        "required": ["bank_iban", "mobile"],
        "unique": "national_id",
        "iban_cols": ["bank_iban"],
        "national_id_cols": ["national_id"],
        "salary_plausible": ("monthly_salary_sar", 3000, 200000),
    },
    "04_citizen_service_requests.csv": {
        "required": ["request_text_ar"],
        "unique": "request_id",
    },
    # Empty current_label = unclassified data (NDMO completeness of classification
    # metadata); such records default to Restricted until reviewed.
    "05_documents_register.csv": {"required": ["current_label"], "unique": "doc_id"},
    "06_open_datasets.csv": {"unique": "record_id"},
}


def _rid(file, row):
    col = ID_COL.get(file)
    return str(row.get(col, "")) if col else ""


def scan_dataframe(file_name: str, df: pd.DataFrame):
    """Return (findings:list[dict], scorecard:dict[dim->metrics])."""
    cfg = RULES.get(file_name, {})
    findings = []
    n = len(df)
    counts = {d: 0 for d in
              ["Completeness", "Uniqueness", "Timeliness", "Validity", "Accuracy", "Consistency"]}

    def add(dim, row, col, defect, desc):
        counts[dim] += 1
        findings.append({"source_file": file_name, "row_id": _rid(file_name, row), "column": col,
                         "dq_dimension": dim, "defect_type": defect, "description": desc})

    for _, row in df.iterrows():
        # Completeness
        for col in cfg.get("required", []):
            if col in df.columns and (pd.isna(row[col]) or str(row[col]).strip() == ""):
                add("Completeness", row, col, "missing_value", f"الحقل المطلوب '{col}' فارغ")
        # Validity — national ID
        for col in cfg.get("national_id_cols", []):
            v = str(row.get(col, "") or "")
            if v and not _luhn_ok(v):
                add("Validity", row, col, "bad_national_id", "هوية وطنية غير صحيحة (Luhn/طول)")
        # Validity — IBAN
        for col in cfg.get("iban_cols", []):
            v = str(row.get(col, "") or "")
            if v and not _iban_ok(v):
                add("Validity", row, col, "bad_iban", "آيبان غير صحيح (mod-97/طول)")
        # Validity — VAT 15 digits
        for col in cfg.get("vat_cols", []):
            v = str(row.get(col, "") or "")
            if v and (len(v) != 15 or not v.isdigit()):
                add("Validity", row, col, "bad_vat", "الرقم الضريبي ليس 15 خانة")
        # Validity — non-negative amounts
        for col in cfg.get("non_negative", []):
            try:
                if float(row[col]) < 0:
                    add("Validity", row, col, "negative_amount", "قيمة سالبة غير صحيحة")
            except (ValueError, TypeError):
                pass
        # Validity — no future dates
        for col in cfg.get("no_future", []):
            try:
                if dt.date.fromisoformat(str(row[col])) > TODAY:
                    add("Validity", row, col, "future_date", "تاريخ في المستقبل")
            except (ValueError, TypeError):
                pass
        # Accuracy — VAT/total arithmetic
        if "accuracy_vat" in cfg:
            sc, vc, tc = cfg["accuracy_vat"]
            try:
                sub, vat, tot = float(row[sc]), float(row[vc]), float(row[tc])
                if sub >= 0:
                    if abs(vat - round(sub * VAT_RATE, 2)) > 1.0:
                        add("Accuracy", row, vc, "wrong_vat", "الضريبة ≠ 15% من الإجمالي الفرعي")
                    if abs(tot - round(sub + vat, 2)) > 1.0:
                        add("Accuracy", row, tc, "wrong_total", "الإجمالي ≠ الفرعي + الضريبة")
            except (ValueError, TypeError):
                pass
        # Accuracy — salary plausibility
        if "salary_plausible" in cfg:
            col, lo, hi = cfg["salary_plausible"]
            try:
                s = float(row[col])
                if s < lo or s > hi:
                    add("Accuracy", row, col, "implausible_salary", "راتب خارج النطاق المعقول")
            except (ValueError, TypeError):
                pass
        # Consistency — allowed value sets
        for col, allowed in cfg.get("consistency", {}).items():
            v = str(row.get(col, "") or "").strip()
            if v and v not in allowed:
                add("Consistency", row, col, "non_standard_value", f"قيمة غير قياسية في '{col}': {v}")

    # Uniqueness — whole-column duplicates
    ucol = cfg.get("unique")
    if ucol and ucol in df.columns:
        dup_mask = df[ucol].astype(str).duplicated(keep=False) & df[ucol].notna()
        for _, row in df[dup_mask].iterrows():
            add("Uniqueness", row, ucol, "duplicate_value", f"قيمة مكررة في '{ucol}'")

    # Timeliness — stale records
    if "timeliness" in cfg:
        col, max_days = cfg["timeliness"]
        if col in df.columns:
            for _, row in df.iterrows():
                try:
                    if (TODAY - dt.date.fromisoformat(str(row[col]))).days > max_days:
                        add("Timeliness", row, col, "stale_record", "لم يُحدّث منذ أكثر من 3 سنوات")
                except (ValueError, TypeError):
                    pass

    scorecard = {
        dim: {"defects": c, "rows": n,
              "score": round(100 * (1 - c / n), 1) if n else 100.0}
        for dim, c in counts.items()
    }
    return findings, scorecard
