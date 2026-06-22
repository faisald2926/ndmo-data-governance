"""Evaluation against the shipped answer keys.

Classification accuracy + confusion matrix vs data/ground_truth_labels.csv.
Quality precision/recall per dimension vs data/quality_issues_log.csv.
"""
import os

import pandas as pd

from config import settings
from db import SessionLocal
from models import Classification, QualityFinding


def _read(name):
    return pd.read_csv(os.path.join(settings.DATA_DIR, name),
                       encoding="utf-8-sig", dtype=str, keep_default_na=False)


def evaluate_classification() -> dict:
    gt = _read("ground_truth_labels.csv")
    session = SessionLocal()
    try:
        preds = {(c.source_file, c.record_id): c.ndmo_level
                 for c in session.query(Classification).all()}
    finally:
        session.close()

    levels = ["عام", "مقيّد", "سري", "سري للغاية"]
    conf = {t: {p: 0 for p in levels} for t in levels}
    n = correct = 0
    for _, r in gt.iterrows():
        key = (r["source_file"], r["record_id"])
        if key not in preds:
            continue                       # not classified in this run (max_per_file)
        true, pred = r["ndmo_level"], preds[key]
        if true in conf and pred in conf[true]:
            conf[true][pred] += 1
        n += 1
        correct += int(true == pred)
    return {
        "evaluated": n,
        "accuracy": round(correct / n, 4) if n else None,
        "confusion_matrix": conf,
        "levels": levels,
    }


def evaluate_quality() -> dict:
    truth_df = _read("quality_issues_log.csv")
    truth = {(r["file"], r["row_id"], r["dq_dimension"]) for _, r in truth_df.iterrows()}

    session = SessionLocal()
    try:
        pred = {(f.source_file, f.row_id, f.dq_dimension)
                for f in session.query(QualityFinding).all()}
    finally:
        session.close()

    dims = ["Completeness", "Uniqueness", "Timeliness", "Validity", "Accuracy", "Consistency"]

    def prf(p, t):
        tp = len(p & t)
        precision = tp / len(p) if p else None
        recall = tp / len(t) if t else None
        return {"tp": tp, "predicted": len(p), "actual": len(t),
                "precision": round(precision, 3) if precision is not None else None,
                "recall": round(recall, 3) if recall is not None else None}

    per_dim = {d: prf({x for x in pred if x[2] == d}, {x for x in truth if x[2] == d})
               for d in dims}
    return {"overall": prf(pred, truth), "by_dimension": per_dim}


def evaluate_all() -> dict:
    return {"classification": evaluate_classification(), "quality": evaluate_quality()}


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate_all(), ensure_ascii=False, indent=2))
