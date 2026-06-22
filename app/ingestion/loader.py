"""CSV ingestion — load source datasets into data_records."""
import os

import pandas as pd

from models import DataRecord
from quality.engine import ID_COL

# The six entity tables that flow through the pipeline.
SOURCE_FILES = [
    "01_vendors_master.csv", "02_invoices.csv", "03_employees_payroll.csv",
    "04_citizen_service_requests.csv", "05_documents_register.csv",
    "06_open_datasets.csv",
]

# How to build the free-text blob the classifier reasons over.
FREE_TEXT = {
    "04_citizen_service_requests.csv": lambda r: str(r.get("request_text_ar", "") or ""),
    "05_documents_register.csv":
        lambda r: f"{r.get('title_ar', '')} {r.get('snippet_ar', '')}".strip(),
}


def read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)


def load_file(session, data_dir: str, file_name: str):
    """Ingest one CSV into data_records; return (df, count)."""
    path = os.path.join(data_dir, file_name)
    df = read_csv(path)
    id_col = ID_COL.get(file_name)
    text_fn = FREE_TEXT.get(file_name)
    rows = []
    for _, row in df.iterrows():
        content = row.to_dict()
        rows.append(DataRecord(
            source_file=file_name,
            record_id=str(content.get(id_col, "")) if id_col else "",
            content=content,
            text_blob=text_fn(content) if text_fn else "",
        ))
    session.bulk_save_objects(rows)
    return df, len(rows)
