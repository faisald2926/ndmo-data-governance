"""Layer 2 — local LLM (ALLaM-7B via Ollama) for free-text / ambiguous content.

Calls Ollama with the NDMO system prompt and forced JSON output. Efficiency:
keep-alive (model stays resident), small context + capped output (fits 8 GB),
and a per-process result cache (the data has many repeated templates). If Ollama
is unreachable and mode is 'auto'/'offline', a transparent keyword classifier
keeps the pipeline running.
"""
import json
import re

import httpx

from config import settings
from . import ndmo
from .system_prompt import build_messages

# --- offline keyword fallback ----------------------------------------------
_KEYWORDS = {
    ndmo.TOP_SECRET: ["عسكري", "عمليات أمنية", "مفاتيح التشفير", "تحركات القوات",
                       "سيادة", "استخبارات", "أسلحة", "منشأة حيوية", "نووي"],
    ndmo.SECRET: ["دبلوماسي", "مذكرة تفاهم", "الميزانية الاستراتيجية", "تحقيق",
                   "قضية", "مواقع تخزين", "معاهدة", "استراتيجية", "قبل الاعتماد"],
    ndmo.RESTRICTED: ["هوية", "راتب", "رواتب", "صحي", "طبي", "عقد مورد", "عرض أسعار",
                       "مذكرة داخلية", "مخطط الشبكة", "خصوصية", "شخصية", "حساب بنكي"],
    ndmo.PUBLIC: ["إعلان", "وظائف", "صحفي", "إحصاءات", "نتائج مالية معلنة",
                   "خدمات", "بيانات مفتوحة", "منشور", "تصريح",
                   "استفسار", "اقتراح", "نسخة", "موعد", "أوقات العمل", "تجديد رخصة"],
}
_IMPACT_BY_LEVEL = {
    ndmo.TOP_SECRET: "المصلحة الوطنية", ndmo.SECRET: "المصلحة الوطنية",
    ndmo.RESTRICTED: "الأفراد", ndmo.PUBLIC: "أنشطة الجهات",
}


def _heuristic(content: str) -> dict:
    text = content or ""
    for level in (ndmo.TOP_SECRET, ndmo.SECRET, ndmo.RESTRICTED, ndmo.PUBLIC):
        for kw in _KEYWORDS[level]:
            if kw in text:
                return {"ndmo_level": level, "impact_category": _IMPACT_BY_LEVEL[level],
                        "impact_level": ndmo.IMPACT_OF_LEVEL[level], "confidence": 0.6,
                        "evidence_span": kw, "rationale_ar": f"تطابق كلمة مفتاحية '{kw}' => {level}",
                        "source": "heuristic"}
    return {"ndmo_level": ndmo.DEFAULT_LEVEL, "impact_category": "أنشطة الجهات",
            "impact_level": ndmo.IMPACT_OF_LEVEL[ndmo.DEFAULT_LEVEL], "confidence": 0.3,
            "evidence_span": "", "rationale_ar": "لا دليل واضح => الافتراضي مقيّد",
            "source": "heuristic"}


def _parse_json(raw: str) -> dict:
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError("no JSON object in model output")
    return json.loads(m.group(0))


def _call_ollama(content: str) -> dict:
    payload = {
        "model": settings.LLM_MODEL,
        "messages": build_messages(content),
        "stream": False,
        "format": "json",
        "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        "options": {"temperature": 0.0,
                    "num_ctx": settings.LLM_NUM_CTX,
                    "num_predict": settings.LLM_NUM_PREDICT},
    }
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = _parse_json(r.json()["message"]["content"])
    if data.get("ndmo_level") not in ndmo.LEVELS:
        data["ndmo_level"] = ndmo.DEFAULT_LEVEL
        data["confidence"] = min(float(data.get("confidence", 0.3)), 0.4)
    data.setdefault("impact_category", _IMPACT_BY_LEVEL.get(data["ndmo_level"], "أنشطة الجهات"))
    data.setdefault("impact_level", ndmo.IMPACT_OF_LEVEL[data["ndmo_level"]])
    data.setdefault("confidence", 0.7)
    data.setdefault("evidence_span", "")
    data.setdefault("rationale_ar", "")
    data["source"] = "allam"
    return data


# Result cache — repeated templates collapse to a handful of real calls.
_CACHE: dict[str, dict] = {}


def classify_text(content: str) -> dict:
    """Classify free text (cached). Honors LLM_MODE: offline | ollama | auto."""
    key = (content or "").strip()
    if key in _CACHE:
        return dict(_CACHE[key])
    result = _classify_uncached(content)
    _CACHE[key] = result
    return dict(result)


def _classify_uncached(content: str) -> dict:
    mode = settings.LLM_MODE.lower()
    if mode == "offline":
        return _heuristic(content)
    try:
        return _call_ollama(content)
    except Exception as exc:                       # noqa: BLE001
        if mode == "ollama":
            raise RuntimeError(f"Ollama unavailable in LLM_MODE=ollama: {exc}") from exc
        result = _heuristic(content)               # auto -> graceful fallback
        result["rationale_ar"] += " (احتياطي: تعذّر الوصول إلى النموذج المحلي)"
        return result


def ensure_model() -> bool:
    """Pull the configured model into Ollama if missing. No-op in offline mode."""
    if settings.LLM_MODE.lower() == "offline":
        return False
    base, model = settings.OLLAMA_BASE_URL, settings.LLM_MODEL
    try:
        with httpx.Client(timeout=15.0) as client:
            tags = client.get(f"{base}/api/tags").json()
            names = {m.get("name", "") for m in tags.get("models", [])}
            if any(model.split(":")[0] in n for n in names):
                return True
            client.post(f"{base}/api/pull", json={"name": model, "stream": False},
                        timeout=None).raise_for_status()
        return True
    except Exception:                              # noqa: BLE001
        return False
