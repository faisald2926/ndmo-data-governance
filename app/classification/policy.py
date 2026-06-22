"""Layer 3 — policy / decision engine.

Combines the rule layer and the LLM layer and enforces NDMO's hard rules:
  * aggregation: take the HIGHEST level present across signals;
  * default: if confidence is low and no rule signal, fall back to Restricted
    and flag needs_review;
  * attach the control recommendation for the final level.
"""
from config import settings
from . import ndmo


def decide(rule_result: dict, llm_result: dict | None) -> dict:
    rule_level = rule_result.get("level") if rule_result else None
    threshold = settings.LLM_CONFIDENCE_THRESHOLD

    if llm_result:
        llm_level = llm_result.get("ndmo_level", ndmo.DEFAULT_LEVEL)
        llm_conf = float(llm_result.get("confidence", 0.0))
        llm_source = llm_result.get("source", "allam")
    else:
        llm_level, llm_conf, llm_source = None, 0.0, None

    # --- aggregation: highest of the two signals --------------------------
    candidates = [lvl for lvl in (rule_level, llm_level) if lvl]
    if candidates:
        final_level = ndmo.highest(candidates)
    else:
        final_level = ndmo.DEFAULT_LEVEL          # nothing fired -> default

    # --- low-confidence / disagreement -> review + safe default -----------
    low_conf = (rule_level is None) and (llm_conf < threshold)
    if low_conf:
        final_level = ndmo.higher(final_level, ndmo.DEFAULT_LEVEL)
    disagree = bool(rule_level and llm_level and rule_level != llm_level)
    needs_review = low_conf or disagree or (llm_source == "heuristic" and llm_conf < threshold)

    # --- provenance & confidence ------------------------------------------
    if final_level == rule_level:
        decided_by, confidence = "rules", rule_result.get("confidence", 0.95)
        impact = rule_result.get("impact_category")
        evidence = rule_result.get("evidence", "")
        rationale = "رصدت طبقة القواعد بيانات حساسة/شخصية."
    elif llm_result and final_level == llm_level:
        decided_by, confidence = llm_source, llm_conf
        impact = llm_result.get("impact_category")
        evidence = llm_result.get("evidence_span", "")
        rationale = llm_result.get("rationale_ar", "")
    else:
        decided_by, confidence = "policy", max(llm_conf, 0.5)
        impact = (rule_result.get("impact_category") if rule_level
                  else (llm_result or {}).get("impact_category")) or "أنشطة الجهات"
        evidence = rule_result.get("evidence", "") or (llm_result or {}).get("evidence_span", "")
        rationale = "طُبّقت قاعدة الأثر الأعلى عند تجميع الإشارات."

    return {
        "ndmo_level": final_level,
        "impact_category": impact or "أنشطة الجهات",
        "impact_level": ndmo.IMPACT_OF_LEVEL[final_level],
        "confidence": round(float(confidence), 3),
        "decided_by": decided_by,
        "evidence": evidence,
        "rationale": rationale,
        "pii_types": (rule_result or {}).get("pii_types", []),
        "control_recommendation": ndmo.CONTROLS[final_level],
        "needs_review": needs_review,
    }
