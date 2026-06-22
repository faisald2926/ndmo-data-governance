"""Lineage tracer — OpenLineage-style events persisted to Postgres.

Demonstrates the NDMO aggregation rule: a report built from Restricted sources
inherits Restricted. The pipeline emits source -> transform -> report events.
"""
from classification import ndmo
from models import LineageEvent


def emit(session, job_name, event_type, inputs, outputs, derived_level=None, note=""):
    ev = LineageEvent(job_name=job_name, event_type=event_type, inputs=inputs,
                      outputs=outputs, derived_level=derived_level, note=note)
    session.add(ev)
    return ev


def record_pipeline_lineage(session, dataset_levels: dict):
    """Build the canonical ingest -> join -> report chain.

    `dataset_levels` maps source_file -> its (highest) classification level.
    The spend report joins invoices + vendors and inherits the highest level.
    """
    inv = "02_invoices.csv"
    ven = "01_vendors_master.csv"
    report_level = ndmo.highest([dataset_levels.get(inv, ndmo.PUBLIC),
                                 dataset_levels.get(ven, ndmo.PUBLIC)])

    emit(session, "ingest_invoices", "COMPLETE",
         inputs=[{"namespace": "files", "name": inv}],
         outputs=[{"namespace": "db", "name": "stg_invoices"}],
         derived_level=dataset_levels.get(inv))
    emit(session, "join_vendor_invoice", "COMPLETE",
         inputs=[{"namespace": "db", "name": "stg_invoices"},
                 {"namespace": "db", "name": "stg_vendors", "source": ven}],
         outputs=[{"namespace": "db", "name": "fact_spend"}],
         derived_level=report_level)
    emit(session, "build_spend_report", "COMPLETE",
         inputs=[{"namespace": "db", "name": "fact_spend"}],
         outputs=[{"namespace": "report", "name": "quarterly_spend_dashboard"}],
         derived_level=report_level,
         note="قاعدة التجميع: التقرير يرث المستوى الأعلى من مصادره => "
              f"{report_level}")
    session.flush()
    return report_level


def to_graph(events):
    """Convert stored events into nodes + edges for the dashboard graph."""
    nodes, edges, seen = [], [], set()

    def node(name, kind, level=None):
        if name not in seen:
            seen.add(name)
            nodes.append({"id": name, "kind": kind, "level": level})

    for ev in events:
        for i in ev.inputs or []:
            node(i["name"], i["namespace"])
        for o in ev.outputs or []:
            node(o["name"], o["namespace"], ev.derived_level)
        node(ev.job_name, "job")
        for i in ev.inputs or []:
            edges.append({"from": i["name"], "to": ev.job_name})
        for o in ev.outputs or []:
            edges.append({"from": ev.job_name, "to": o["name"]})
    return {"nodes": nodes, "edges": edges}
