"""SQLAlchemy ORM models — the governance store."""
import datetime as dt

from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, JSON,
                        String, Text)

from db import Base


def _now():
    return dt.datetime.now(dt.timezone.utc)


class DataRecord(Base):
    """A single ingested row or document from a source dataset."""
    __tablename__ = "data_records"

    id = Column(Integer, primary_key=True)
    source_file = Column(String(128), index=True)
    record_id = Column(String(64), index=True)      # business id (e.g. INV-2026-00001)
    content = Column(JSON)                           # the row as a dict
    text_blob = Column(Text)                         # concatenated text for free-text rows
    ingested_at = Column(DateTime, default=_now)


class Classification(Base):
    """The NDMO classification decision for a record."""
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True)
    source_file = Column(String(128), index=True)
    record_id = Column(String(64), index=True)
    ndmo_level = Column(String(32), index=True)      # سري للغاية | سري | مقيّد | عام
    impact_category = Column(String(64))
    impact_level = Column(String(32))                # عالي | متوسط | منخفض | لا يوجد
    confidence = Column(Float)
    decided_by = Column(String(32))                  # rules | allam | heuristic | policy
    evidence = Column(Text)                          # the span/signal that triggered it
    rationale = Column(Text)
    pii_types = Column(JSON)                          # list of detected PII types
    control_recommendation = Column(Text)
    needs_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)


class QualityFinding(Base):
    """A data-quality defect detected by the quality engine."""
    __tablename__ = "quality_findings"

    id = Column(Integer, primary_key=True)
    source_file = Column(String(128), index=True)
    row_id = Column(String(64), index=True)
    column = Column(String(64))
    dq_dimension = Column(String(32), index=True)    # one of the 6 NDMO dimensions
    defect_type = Column(String(64))
    description = Column(Text)
    created_at = Column(DateTime, default=_now)


class LineageEvent(Base):
    """An OpenLineage-style event: a job consuming inputs and producing outputs."""
    __tablename__ = "lineage_events"

    id = Column(Integer, primary_key=True)
    job_name = Column(String(128), index=True)
    event_type = Column(String(32))                  # START | COMPLETE
    inputs = Column(JSON)                            # [{namespace, name}]
    outputs = Column(JSON)
    derived_level = Column(String(32))               # highest level across inputs
    note = Column(Text)
    created_at = Column(DateTime, default=_now)


class AuditLog(Base):
    """Append-only audit trail of governance actions."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    action = Column(String(64), index=True)
    detail = Column(JSON)
    created_at = Column(DateTime, default=_now)
