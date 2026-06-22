"""NDMO Data Governance — Streamlit dashboard (easy, extensible).

Talks to the FastAPI backend over HTTP. Tabs: Overview, Records, Quality,
Evaluation, Lineage, Live classify.
"""
import os

import pandas as pd
import requests
import streamlit as st

API = os.environ.get("API_URL", "http://localhost:8000")
LEVELS = ["عام", "مقيّد", "سري", "سري للغاية"]

st.set_page_config(page_title="NDMO Data Governance", page_icon="🛡️", layout="wide")


def api_get(path, **params):
    try:
        r = requests.get(f"{API}{path}", params=params, timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception as e:                       # noqa: BLE001
        st.error(f"GET {path} failed: {e}")
        return None


def api_post(path, json=None):
    try:
        r = requests.post(f"{API}{path}", json=json or {}, timeout=1800)
        r.raise_for_status()
        return r.json()
    except Exception as e:                       # noqa: BLE001
        st.error(f"POST {path} failed: {e}")
        return None


# --- sidebar ---------------------------------------------------------------
st.sidebar.title("🛡️ NDMO Governance")
health = api_get("/health")
if health:
    st.sidebar.success(f"API up · LLM: {health['llm_mode']} · {health['model']}")
st.sidebar.markdown("### تشغيل خط المعالجة")
max_pf = st.sidebar.number_input("Max rows per file (0 = all)", 0, 20000, 300, step=100)
if st.sidebar.button("▶️ Run pipeline", use_container_width=True):
    with st.spinner("Ingest → classify → quality → lineage…"):
        res = api_post("/pipeline/run", {"max_per_file": (max_pf or None)})
    if res:
        st.sidebar.success(f"Done · {res.get('quality_findings', 0)} quality findings")
        st.session_state["ran"] = True

st.title("لوحة حوكمة البيانات — NDMO")
tabs = st.tabs(["نظرة عامة", "السجلات", "الجودة", "التقييم", "الأثر (Lineage)", "تصنيف مباشر"])

# --- Overview --------------------------------------------------------------
with tabs[0]:
    stats = api_get("/stats")
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", stats["total_records"])
        c2.metric("Classified", stats["classified"])
        c3.metric("Needs review", stats["needs_review"])
        c4.metric("Quality findings", sum(stats["quality_findings_by_dimension"].values()) or 0)
        st.subheader("توزيع مستويات التصنيف")
        lvl = stats["classification_by_level"] or {}
        st.bar_chart(pd.Series({k: lvl.get(k, 0) for k in LEVELS}, name="count"))
        st.subheader("مشاكل الجودة حسب البُعد")
        dim = stats["quality_findings_by_dimension"] or {}
        if dim:
            st.bar_chart(pd.Series(dim, name="defects"))
    else:
        st.info("Run the pipeline from the sidebar to populate the dashboard.")

# --- Records ---------------------------------------------------------------
with tabs[1]:
    col1, col2 = st.columns(2)
    flevel = col1.selectbox("Level", ["(الكل)"] + LEVELS)
    fsource = col2.text_input("Source file contains", "")
    params = {"limit": 200}
    if flevel != "(الكل)":
        params["level"] = flevel
    if fsource:
        params["source_file"] = fsource
    rows = api_get("/records", **params)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=520)
    else:
        st.info("No records yet.")

# --- Quality ---------------------------------------------------------------
with tabs[2]:
    dim = st.selectbox("Dimension", ["(الكل)", "Completeness", "Uniqueness",
                                     "Timeliness", "Validity", "Accuracy", "Consistency"])
    params = {"limit": 500}
    if dim != "(الكل)":
        params["dimension"] = dim
    finds = api_get("/quality/findings", **params)
    if finds:
        st.dataframe(pd.DataFrame(finds), use_container_width=True, height=520)
    else:
        st.info("No quality findings yet.")

# --- Evaluation ------------------------------------------------------------
with tabs[3]:
    st.caption("Scores the last pipeline run against the shipped answer keys.")
    if st.button("Run evaluation"):
        ev = api_get("/evaluate")
        if ev:
            cls = ev["classification"]
            st.metric("Classification accuracy",
                      f"{cls['accuracy']:.1%}" if cls["accuracy"] is not None else "—",
                      help=f"{cls['evaluated']} records evaluated")
            st.subheader("مصفوفة الالتباس (صحيح ↓ / متوقع →)")
            cm = pd.DataFrame(cls["confusion_matrix"]).T.reindex(index=cls["levels"],
                                                                columns=cls["levels"])
            st.dataframe(cm, use_container_width=True)
            st.subheader("جودة البيانات: الدقة والاسترجاع")
            q = ev["quality"]["by_dimension"]
            st.dataframe(pd.DataFrame(q).T, use_container_width=True)
            st.caption(f"Overall quality — precision "
                       f"{ev['quality']['overall']['precision']}, "
                       f"recall {ev['quality']['overall']['recall']}")

# --- Lineage ---------------------------------------------------------------
with tabs[4]:
    lin = api_get("/lineage")
    if lin and lin["events"]:
        for e in lin["events"]:
            st.write(f"**{e['job']}** → `{e['derived_level']}`  {e.get('note', '')}")
        dot = ["digraph G { rankdir=LR; node [shape=box, style=rounded];"]
        for n in lin["graph"]["nodes"]:
            label = n["id"] + (f"\\n[{n['level']}]" if n.get("level") else "")
            dot.append(f'"{n["id"]}" [label="{label}"];')
        for ed in lin["graph"]["edges"]:
            dot.append(f'"{ed["from"]}" -> "{ed["to"]}";')
        dot.append("}")
        st.graphviz_chart("\n".join(dot))
    else:
        st.info("No lineage yet — run the pipeline.")

# --- Live classify ---------------------------------------------------------
with tabs[5]:
    st.caption("جرّب التصنيف مباشرة عبر الطبقات الثلاث (قواعد + النموذج المحلي + السياسة).")
    txt = st.text_area("النص", "أعاني من حالة صحية وأطلب إعفاءً، هويتي 1043215789")
    if st.button("صنّف"):
        res = api_post("/classify", {"text": txt})
        if res:
            c1, c2, c3 = st.columns(3)
            c1.metric("المستوى", res["ndmo_level"])
            c2.metric("الثقة", res["confidence"])
            c3.metric("مراجعة بشرية", "نعم" if res["needs_review"] else "لا")
            st.json(res)
