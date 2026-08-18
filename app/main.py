"""FastAPI app — REST API (role-protected) + the bilingual web frontend."""
import os

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

import auth
import evaluate as evaluator
import pipeline as pipeline_mod
from classification import classifier, ndmo
from config import settings
from db import get_session, init_db
from ingestion.seed_postgres import seed as seed_postgres
from lineage import tracer
from models import (AuditLog, Classification, DataRecord, LineageEvent,
                    QualityFinding, User)
from schemas import (ClassifyRequest, LoginRequest, PipelineRequest,
                     RecordUpdate, UserCreate)

app = FastAPI(title="NDMO Data Governance API", version="2.0.0",
              description="Automated NDMO classification + quality + lineage, with RBAC.")

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.on_event("startup")
def _startup():
    init_db()
    auth.seed_users()


@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_session)):
    user = db.query(User).filter_by(username=req.username).first()
    if not user or not auth.verify_password(req.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
    return {"access_token": auth.create_token(user.username, user.role),
            "token_type": "bearer", "username": user.username, "role": user.role}


@app.get("/auth/me")
def me(user: dict = Depends(auth.get_current_user)):
    return user


@app.get("/users")
def list_users(_: dict = Depends(auth.require_admin), db: Session = Depends(get_session)):
    return [{"id": u.id, "username": u.username, "role": u.role,
             "created_at": u.created_at.isoformat() if u.created_at else None}
            for u in db.query(User).order_by(User.id).all()]


@app.post("/users", status_code=201)
def create_user(body: UserCreate, _: dict = Depends(auth.require_admin),
                db: Session = Depends(get_session)):
    if body.role not in ("admin", "viewer"):
        raise HTTPException(400, "role must be 'admin' or 'viewer'")
    if db.query(User).filter_by(username=body.username).first():
        raise HTTPException(409, "username already exists")
    u = User(username=body.username, password_hash=auth.hash_password(body.password),
             role=body.role)
    db.add(u)
    db.add(AuditLog(action="user_create", detail={"username": body.username, "role": body.role}))
    db.commit()
    return {"id": u.id, "username": u.username, "role": u.role}


@app.delete("/users/{user_id}")
def delete_user(user_id: int, admin: dict = Depends(auth.require_admin),
                db: Session = Depends(get_session)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(404, "user not found")
    if u.username == admin["username"]:
        raise HTTPException(400, "you cannot delete your own account")
    db.delete(u)
    db.add(AuditLog(action="user_delete", detail={"username": u.username}))
    db.commit()
    return {"deleted": u.username}


@app.post("/classify")
def classify(req: ClassifyRequest, _: dict = Depends(auth.get_current_user)):
    return classifier.classify_record(req.content or {}, req.text or "")


@app.patch("/records/{record_pk}")
def update_record(record_pk: int, body: RecordUpdate,
                  admin: dict = Depends(auth.require_admin),
                  db: Session = Depends(get_session)):
    rec = db.query(Classification).get(record_pk)
    if not rec:
        raise HTTPException(404, "record not found")
    changes = {}
    if body.ndmo_level is not None:
        if body.ndmo_level not in ndmo.LEVELS:
            raise HTTPException(400, f"ndmo_level must be one of {ndmo.LEVELS}")
        rec.ndmo_level = body.ndmo_level
        rec.impact_level = ndmo.IMPACT_OF_LEVEL[body.ndmo_level]
        rec.control_recommendation = ndmo.CONTROLS[body.ndmo_level]
        rec.decided_by = "admin"
        changes["ndmo_level"] = body.ndmo_level
    if body.needs_review is not None:
        rec.needs_review = body.needs_review
        changes["needs_review"] = body.needs_review
    db.add(AuditLog(action="record_update",
                    detail={"record_pk": record_pk, "by": admin["username"], **changes}))
    db.commit()
    return {"id": rec.id, "ndmo_level": rec.ndmo_level, "needs_review": rec.needs_review,
            "decided_by": rec.decided_by}


@app.post("/pipeline/run")
def run_pipeline(req: PipelineRequest, _: dict = Depends(auth.require_admin)):
    return pipeline_mod.run(max_per_file=req.max_per_file)


@app.post("/data/seed")
def seed_data(_: dict = Depends(auth.require_admin)):
    return {"seeded": seed_postgres()}


@app.get("/stats")
def stats(_: dict = Depends(auth.get_current_user), db: Session = Depends(get_session)):
    by_level = dict(db.query(Classification.ndmo_level, func.count())
                    .group_by(Classification.ndmo_level).all())
    by_dim = dict(db.query(QualityFinding.dq_dimension, func.count())
                  .group_by(QualityFinding.dq_dimension).all())
    needs_review = db.query(func.count()).select_from(Classification)\
        .filter(Classification.needs_review.is_(True)).scalar()
    return {"total_records": db.query(func.count()).select_from(DataRecord).scalar(),
            "classified": db.query(func.count()).select_from(Classification).scalar(),
            "classification_by_level": by_level, "needs_review": needs_review,
            "quality_findings_by_dimension": by_dim}


@app.get("/records")
def records(level: str | None = None, source_file: str | None = None,
            needs_review: bool | None = None, limit: int = Query(50, le=500), offset: int = 0,
            _: dict = Depends(auth.get_current_user), db: Session = Depends(get_session)):
    q = db.query(Classification)
    if level:
        q = q.filter(Classification.ndmo_level == level)
    if source_file:
        q = q.filter(Classification.source_file == source_file)
    if needs_review is not None:
        q = q.filter(Classification.needs_review.is_(needs_review))
    # Rows are written one source file at a time, so plain id order returns a
    # single dataset. Interleave by file instead, so the first page is a real
    # cross-section of all nine sources (and of all four levels).
    rank = func.row_number().over(partition_by=Classification.source_file,
                                  order_by=Classification.id)
    rows = (q.order_by(rank, Classification.source_file)
             .offset(offset).limit(limit).all())
    return [{"id": r.id, "source_file": r.source_file, "record_id": r.record_id,
             "ndmo_level": r.ndmo_level, "impact_category": r.impact_category,
             "confidence": r.confidence, "decided_by": r.decided_by, "evidence": r.evidence,
             "rationale": r.rationale, "needs_review": r.needs_review,
             "control_recommendation": r.control_recommendation} for r in rows]


@app.get("/quality/findings")
def quality_findings(dimension: str | None = None, source_file: str | None = None,
                     limit: int = Query(100, le=1000),
                     _: dict = Depends(auth.get_current_user), db: Session = Depends(get_session)):
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
def lineage(_: dict = Depends(auth.get_current_user), db: Session = Depends(get_session)):
    events = db.query(LineageEvent).all()
    return {"graph": tracer.to_graph(events),
            "events": [{"job": e.job_name, "derived_level": e.derived_level,
                        "note": e.note} for e in events]}


@app.get("/evaluate")
def evaluate_endpoint(_: dict = Depends(auth.get_current_user)):
    return evaluator.evaluate_all()


@app.get("/health")
def health():
    return {"status": "ok", "llm_mode": settings.LLM_MODE, "model": settings.LLM_MODEL}


if os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))
