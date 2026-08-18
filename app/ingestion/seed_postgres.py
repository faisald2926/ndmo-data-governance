"""Load the generated datasets into PostgreSQL as queryable tables.

Creates one raw_* table per source dataset plus the three answer-key tables,
so the data lives natively in Postgres (not just CSV). Idempotent: re-running
replaces the tables.

Run:  python seed_postgres.py [--data-dir /data]
Make: make seed-data
"""
import argparse
import os

import pandas as pd

from config import settings
from db import engine

# source CSV  ->  Postgres table name
TABLES = {
    "01_vendors_master.csv": "raw_vendors",
    "02_invoices.csv": "raw_invoices",
    "03_employees_payroll.csv": "raw_employees",
    "04_citizen_service_requests.csv": "raw_citizen_requests",
    "05_documents_register.csv": "raw_documents",
    "06_open_datasets.csv": "raw_open_datasets",
    "08_security_incidents.csv": "raw_security_incidents",
    "09_internal_investigations.csv": "raw_internal_investigations",
    "10_strategic_initiatives.csv": "raw_strategic_initiatives",
    "data_dictionary_ndmo.csv": "data_dictionary",
    "ground_truth_labels.csv": "ground_truth_labels",
    "quality_issues_log.csv": "quality_issues_log",
}


def seed(data_dir: str | None = None) -> dict:
    data_dir = data_dir or settings.DATA_DIR
    counts = {}
    for csv_name, table in TABLES.items():
        path = os.path.join(data_dir, csv_name)
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
        df.to_sql(table, engine, if_exists="replace", index=False,
                  method="multi", chunksize=500)
        counts[table] = len(df)
    return counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    result = seed(args.data_dir)
    import json
    print("Seeded PostgreSQL tables:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
