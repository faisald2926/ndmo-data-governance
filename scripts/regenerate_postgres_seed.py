#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild db/postgres_seed.sql from the CSVs in data/.

The seed is the bootstrap Postgres image; it must stay in step with the CSVs,
otherwise a fresh `docker compose up` serves the pre-expansion corpus while the
pipeline reads the expanded one. Mirrors the table map in
app/ingestion/seed_postgres.py.

Run:  python scripts/regenerate_postgres_seed.py
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "db", "postgres_seed.sql")

TABLES = [
    ("01_vendors_master.csv", "raw_vendors"),
    ("02_invoices.csv", "raw_invoices"),
    ("03_employees_payroll.csv", "raw_employees"),
    ("04_citizen_service_requests.csv", "raw_citizen_requests"),
    ("05_documents_register.csv", "raw_documents"),
    ("06_open_datasets.csv", "raw_open_datasets"),
    ("08_security_incidents.csv", "raw_security_incidents"),
    ("09_internal_investigations.csv", "raw_internal_investigations"),
    ("10_strategic_initiatives.csv", "raw_strategic_initiatives"),
    ("data_dictionary_ndmo.csv", "data_dictionary"),
    ("ground_truth_labels.csv", "ground_truth_labels"),
    ("quality_issues_log.csv", "quality_issues_log"),
]

BATCH = 300


def q(v):
    return "'" + str(v).replace("'", "''") + "'"


def main():
    counts = {}
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("-- NDMO Data Governance - PostgreSQL seed (auto-generated, synthetic data)\n")
        fh.write("SET client_encoding = 'UTF8';\nBEGIN;\n\n")
        for csv_name, table in TABLES:
            path = os.path.join(DATA, csv_name)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8-sig", newline="") as src:
                rdr = csv.reader(src)
                header = next(rdr)
                rows = list(rdr)
            cols = ", ".join(f'"{c}"' for c in header)
            fh.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
            fh.write(f"CREATE TABLE {table} ("
                     + ", ".join(f'"{c}" TEXT' for c in header) + ");\n")
            for i in range(0, len(rows), BATCH):
                chunk = rows[i:i + BATCH]
                fh.write(f"INSERT INTO {table} ({cols}) VALUES\n")
                fh.write(",\n".join("(" + ", ".join(q(v) for v in r) + ")" for r in chunk))
                fh.write(";\n")
            fh.write("\n")
            counts[table] = len(rows)
        fh.write("COMMIT;\n")
    for t, n in counts.items():
        print(f"{t:32s} {n:6d}")
    print(f"{'TOTAL':32s} {sum(counts.values()):6d}  ->  {OUT}")


if __name__ == "__main__":
    main()
