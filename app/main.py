"""FastAPI app — REST surface over the governance engines."""
from fastapi import Depends, FastAPI, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

import evaluate as evaluator
import pipeline as pipeline_mod
from ingestion.seed_postgres import seed as seed_postgres
from classification import classifier
from config import settings
from db import get_session, init_db
from lineage import tracer
from models import Classification, DataRecord, LineageEvent, QualityFinding
from schemas import ClassifyRequest, PipelineRequest

app = FastAPI(title="NDMO Data Governance API", version="1.0.0",
              description="Automated NDMO classification + data-quality + lineage.")


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "llm_mode": settings.LLM_MODE, "model": settings.LLM_MODEL}


@app.post("/classify")
def classify(req: ClassifyRequest):
    """Classify a single text or structured record (live; not stored)."""
    return classifier.classify_record(req.content or {}, req.text or "")


@app.post("/pipeline/run")
def run_pipeline(req: PipelineRequest):
    """Ingest -> classify -> quality -> lineage over the mounted datasets."""
    return pipeline_mod.run(max_per_file=req.max_per_file)


@app.post("/data/seed")
def seed_data():
    """Load the CSV datasets into Postgres tables (raw_* + answer keys)."""
    return {"seeded": seed_postgres()}


@app.get("/stats")
def stats(db: Session = Depends(get_session)):
    by_level = dict(db.query(Classification.ndmo_level, func.count())
                    .group_by(Classification.ndmo_level).all())
    by_dim = dict(db.query(QualityFinding.dq_dimension, func.count())
                  .group_by(QualityFinding.dq_dimension).all())
    needs_review = db.query(func.count()).select_from(Classification)\
        .filter(Classification.needs_review.is_(True)).scalar()
    return {
        "total_records": db.query(func.count()).select_from(DataRecord).scalar(),
        "classified": db.query(func.count()).select_from(Classification).scalar(),
        "classification_by_level": by_level,
        "needs_review": needs_review,
        "quality_findings_by_dimension": by_dim,
    }


@app.get("/records")
def records(level: str | None = None, source_file: str | None = None,
            limit: int = Query(50, le=500), offset: int = 0,
            db: Session = Depends(get_session)):
    q = db.query(Classification)
    if level:
        q = q.filter(Classification.ndmo_level == level)
    if source_file:
        q = q.filter(Classification.source_file == source_file)
    rows = q.offset(offset).limit(limit).all()
    return [{"source_file": r.source_file, "record_id": r.record_id,
             "ndmo_level": r.ndmo_level, "impact_category": r.impact_category,
             "confidence": r.confidence, "decided_by": r.decided_by,
             "evidence": r.evidence, "rationale": r.rationale,
             "needs_review": r.needs_review,
             "control_recommendation": r.control_recommendation} for r in rows]


@app.get("/quality/findings")
def quality_findings(dimension: str | None = None, source_file: str | None = None,
                     limit: int = Query(100, le=1000),
                     db: Session = Depends(get_session)):
    q = db.query(QualityFinding)
    if dimension:
        q = q.filter(QualityFinding.dq_dimension == dimension)
    if source_file:
        q = q.filter(QualityFinding.source_file == source_file)
    rows = q.limit(limit).all()
    return [{"file": r.source_file, "row_id": r.row_id, "column": r.column,
             "dq_dimension": r.dq_dimension, "defect_type": r.defect_type,
             "description": r.description} for r in rows]


@app.get("/lineage")
def lineage(db: Session = Depends(get_session)):
    events = db.query(LineageEvent).all()
    return {"graph": tracer.to_graph(events),
            "events": [{"job": e.job_name, "derived_level": e.derived_level,
                        "note": e.note} for e in events]}


@app.get("/evaluate")
def evaluate_endpoint():
    """Score the last pipeline run against the shipped answer keys."""
    return evaluator.evaluate_all()
