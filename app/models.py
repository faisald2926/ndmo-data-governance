"""SQLAlchemy ORM models — the governance store."""
import datetime as dt

from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, JSON,
                        String, Text)

from db import Base


def _now():
    return dt.datetime.now(dt.timezone.utc)


class DataRecord(Base):
    __tablename__ = "data_records"
    id = Column(Integer, primary_key=True)
    source_file = Column(String(128), index=True)
    record_id = Column(String(64), index=True)
    content = Column(JSON)
    text_blob = Column(Text)
    ingested_at = Column(DateTime, default=_now)


class Classification(Base):
    __tablename__ = "classifications"
    id = Column(Integer, primary_key=True)
    source_file = Column(String(128), index=True)
    record_id = Column(String(64), index=True)
    ndmo_level = Column(String(32), index=True)
    impact_category = Column(String(64))
    impact_level = Column(String(32))
    confidence = Column(Float)
    decided_by = Column(String(32))
    evidence = Column(Text)
    rationale = Column(Text)
    pii_types = Column(JSON)
    control_recommendation = Column(Text)
    needs_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)


class QualityFinding(Base):
    __tablename__ = "quality_findings"
    id = Column(Integer, primary_key=True)
    source_file = Column(String(128), index=True)
    row_id = Column(String(64), index=True)
    column = Column(String(64))
    dq_dimension = Column(String(32), index=True)
    defect_type = Column(String(64))
    description = Column(Text)
    created_at = Column(DateTime, default=_now)


class LineageEvent(Base):
    __tablename__ = "lineage_events"
    id = Column(Integer, primary_key=True)
    job_name = Column(String(128), index=True)
    event_type = Column(String(32))
    inputs = Column(JSON)
    outputs = Column(JSON)
    derived_level = Column(String(32))
    note = Column(Text)
    created_at = Column(DateTime, default=_now)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    action = Column(String(64), index=True)
    detail = Column(JSON)
    created_at = Column(DateTime, default=_now)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(16), default="viewer")
    created_at = Column(DateTime, default=_now)
