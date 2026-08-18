"""Layer 3 — policy / decision engine.

Combines the rule layer and the LLM layer and enforces NDMO's hard rules:
  * aggregation: take the HIGHEST level present across signals;
  * default: if confidence is low and no rule signal, fall back to Restricted
    and flag needs_review;
  * attach the control recommendation for the final level.
"""
from config import settings
from . import ndmo


def decide(rule_result: dict, llm_result: dict | None,
           keyword_result: dict | None = None) -> dict:
    rule_level = rule_result.get("level") if rule_result else None
    threshold = settings.LLM_CONFIDENCE_THRESHOLD

    # Safety net: the keyword pass may only ever escalate a record INTO
    # «سري للغاية». Letting it vote on the lower levels wrecks «عام» precision
    # (measured: overall accuracy falls to 77%), so its authority is deliberately
    # narrowed to the one level where the model under-calls and the cost of a
    # miss is a national-interest breach rather than mere friction.
    kw_level = (keyword_result or {}).get("ndmo_level")
    kw_escalates = kw_level == ndmo.TOP_SECRET

    if llm_result:
        llm_level = llm_result.get("ndmo_level", ndmo.DEFAULT_LEVEL)
        llm_conf = float(llm_result.get("confidence", 0.0))
        llm_source = llm_result.get("source", "allam")
    else:
        llm_level, llm_conf, llm_source = None, 0.0, None

    # --- aggregation: highest of the two signals --------------------------
    candidates = [lvl for lvl in (rule_level, llm_level) if lvl]
    if kw_escalates:
        candidates.append(kw_level)
    if candidates:
        final_level = ndmo.highest(candidates)
    else:
        final_level = ndmo.DEFAULT_LEVEL          # nothing fired -> default

    # --- low-confidence / disagreement -> review + safe default -----------
    low_conf = (rule_level is None) and (llm_conf < threshold)
    if low_conf:
        final_level = ndmo.higher(final_level, ndmo.DEFAULT_LEVEL)
    disagree = bool(rule_level and llm_level and rule_level != llm_level)
    # A safety-net escalation overrides the model on the most sensitive level —
    # always put a human on it.
    kw_override = bool(kw_escalates and llm_level and llm_level != ndmo.TOP_SECRET)
    needs_review = (low_conf or disagree or kw_override
                    or (llm_source == "heuristic" and llm_conf < threshold))

    # --- provenance & confidence ------------------------------------------
    if kw_escalates and final_level == ndmo.TOP_SECRET and llm_level != ndmo.TOP_SECRET:
        decided_by, confidence = "keywords:safety-net", 0.75
        impact = keyword_result.get("impact_category", "المصلحة الوطنية")
        evidence = keyword_result.get("evidence_span", "")
        rationale = ("شبكة أمان الكلمات المفتاحية رفعت التصنيف إلى «سري للغاية» "
                     f"استنادًا إلى '{keyword_result.get('evidence_span', '')}' "
                     "بينما صنّفه النموذج أدنى من ذلك.")
    elif final_level == rule_level:
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
