"""End-to-end governance pipeline: ingest -> classify -> quality -> lineage.

Run as a script:   python pipeline.py [--max-per-file N] [--data-dir /data]
Or call run() from the API. Free-text classification is parallelised across
LLM_CONCURRENCY workers (Ollama calls are I/O-bound).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor

from classification import classifier, llm, ndmo
from config import settings
from db import SessionLocal, init_db
from ingestion.loader import FREE_TEXT, SOURCE_FILES, load_file
from models import (AuditLog, Classification, DataRecord, LineageEvent,
                    QualityFinding)
from quality.engine import ID_COL, scan_dataframe
from lineage import tracer

# Classify-by-source rule: open-data portal content is Public by definition.
SOURCE_LEVEL_RULES = {"06_open_datasets.csv": ndmo.PUBLIC}


def _reset(session):
    for model in (Classification, QualityFinding, LineageEvent, DataRecord, AuditLog):
        session.query(model).delete()
    session.commit()


def _classify_file(session, file_name, df, max_per_file):
    id_col = ID_COL.get(file_name)
    text_fn = FREE_TEXT.get(file_name)
    sub = df.head(max_per_file) if max_per_file else df
    forced = SOURCE_LEVEL_RULES.get(file_name)

    rows = [r.to_dict() for _, r in sub.iterrows()]

    def classify_one(content):
        if forced:
            return {"ndmo_level": forced, "impact_category": "أنشطة الجهات",
                    "impact_level": ndmo.IMPACT_OF_LEVEL[forced], "confidence": 0.99,
                    "decided_by": "rules:source", "evidence": "مصدر: بوابة بيانات مفتوحة",
                    "rationale": "بيانات منشورة كبيانات مفتوحة => عام", "pii_types": [],
                    "control_recommendation": ndmo.CONTROLS[forced], "needs_review": False}
        return classifier.classify_record(content, text_fn(content) if text_fn else "")

    # Parallelise (helps the free-text/Ollama path; harmless for structured rows).
    if forced or not text_fn:
        results = [classify_one(c) for c in rows]
    else:
        with ThreadPoolExecutor(max_workers=max(1, settings.LLM_CONCURRENCY)) as ex:
            results = list(ex.map(classify_one, rows))

    objs = [Classification(source_file=file_name,
                           record_id=str(c.get(id_col, "")) if id_col else "", **res)
            for c, res in zip(rows, results)]
    session.bulk_save_objects(objs)
    session.commit()
    return len(objs)


def run(data_dir: str | None = None, max_per_file: int | None = None) -> dict:
    data_dir = data_dir or settings.DATA_DIR
    init_db()
    model_ready = llm.ensure_model()              # auto-pull ALLaM if missing
    session = SessionLocal()
    summary = {"ingested": {}, "classified": {}, "quality_findings": 0,
               "data_dir": data_dir, "llm_mode": settings.LLM_MODE,
               "model_ready": model_ready}
    try:
        _reset(session)
        dataset_levels = {}
        for fname in SOURCE_FILES:
            df, n = load_file(session, data_dir, fname)
            session.commit()
            summary["ingested"][fname] = n

            summary["classified"][fname] = _classify_file(session, fname, df, max_per_file)

            findings, _ = scan_dataframe(fname, df)
            session.bulk_save_objects([QualityFinding(**f) for f in findings])
            session.commit()
            summary["quality_findings"] += len(findings)

            top = (session.query(Classification.ndmo_level)
                   .filter(Classification.source_file == fname).all())
            dataset_levels[fname] = ndmo.highest([t[0] for t in top]) if top else ndmo.PUBLIC

        report_level = tracer.record_pipeline_lineage(session, dataset_levels)
        session.add(AuditLog(action="pipeline_run",
                             detail={**summary, "report_level": report_level}))
        session.commit()
        summary["report_level"] = report_level
        return summary
    finally:
        session.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--max-per-file", type=int, default=None)
    args = ap.parse_args()
    result = run(args.data_dir, args.max_per_file)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
