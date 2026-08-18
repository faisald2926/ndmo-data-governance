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


# --- reading the model's answer ---------------------------------------------
# `format=json` keeps Ollama's output syntactically valid most of the time, but
# not always: the generation budget can cut a response mid-object, the level can
# come back in a different Arabic spelling (or in English), and confidence can
# arrive as a string or a percentage. Untreated, the first case aborts a whole
# LLM_MODE=ollama run and the other two silently become 'مقيّد'.

_TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_PUNCT = re.compile(r"[«»\"'`.،,:;()\[\]_\-]")


def _norm_ar(s) -> str:
    """Fold Arabic orthography so two spellings of a label compare equal."""
    s = _TASHKEEL.sub("", str(s))
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"),
                 ("ة", "ه"), ("ى", "ي"), ("ؤ", "و"), ("ئ", "ي")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", s)).strip().lower()


# Spellings of the four LEVEL NAMES only — orthographic variants plus the English
# equivalents the model sometimes emits. Not content cues: nothing here maps
# document wording to a level, only one spelling of a label to another.
_LEVEL_SYNONYMS = {
    ndmo.PUBLIC: ["عام", "عامة", "علني", "public", "unclassified"],
    ndmo.RESTRICTED: ["مقيّد", "مقيد", "مقيدة", "restricted", "internal"],
    ndmo.SECRET: ["سري", "سرية", "secret", "confidential"],
    ndmo.TOP_SECRET: ["سري للغاية", "سري جدا", "سري جداً", "top secret",
                      "highly confidential", "strictly confidential"],
}
# Longest first, so 'سري للغاية' is never matched as a bare 'سري'.
_LEVEL_LOOKUP = sorted(
    ((_norm_ar(v), lvl) for lvl, vs in _LEVEL_SYNONYMS.items() for v in vs),
    key=lambda kv: -len(kv[0]))


def _canon_level(value):
    """Map a model-supplied level string onto a canonical NDMO level, or None."""
    if not value:
        return None
    norm = _norm_ar(value)
    for key, lvl in _LEVEL_LOOKUP:
        if norm == key:
            return lvl
    for key, lvl in _LEVEL_LOOKUP:            # tolerate extra words around it
        if key in norm:
            return lvl
    return None


_CONF_WORDS = {"عالي": 0.9, "عالية": 0.9, "مرتفع": 0.9, "high": 0.9,
               "متوسط": 0.7, "متوسطة": 0.7, "medium": 0.7,
               "منخفض": 0.4, "منخفضة": 0.4, "low": 0.4}


def _coerce_confidence(value, default: float = 0.7) -> float:
    """Accept 0.9 | '0.9' | '90%' | 95 | 'عالي' and return a float in [0, 1]."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        num = float(value)
    elif isinstance(value, str):
        try:
            num = float(value.strip().rstrip("%").strip())
            if "%" in value:
                num /= 100.0
        except ValueError:
            num = _CONF_WORDS.get(_norm_ar(value))
            if num is None:
                return default
    else:
        return default
    if num > 1.0:                              # 95, or 90% written as a whole number
        num = num / 100.0 if num <= 100.0 else 1.0
    return min(max(num, 0.0), 1.0)


def _repair_json(raw: str) -> dict:
    """Recover an object from output the generation budget cut short."""
    start = raw.find("{")
    if start < 0:
        raise ValueError("no JSON object in model output")
    text = raw[start:]
    # Close the object at the end, then at each earlier comma boundary.
    for cut in [len(text)] + [i for i, ch in enumerate(text) if ch == ","][::-1]:
        head = text[:cut].rstrip().rstrip(",")
        for suffix in ('}', '"}', '"]}'):
            try:
                obj = json.loads(head + suffix)
            except Exception:                  # noqa: BLE001
                continue
            if isinstance(obj, dict) and obj:
                return obj
    raise ValueError("could not repair truncated JSON")


def _parse_json(raw: str) -> dict:
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return _repair_json(raw)


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
    level = _canon_level(data.get("ndmo_level"))
    if level is None:
        data["ndmo_level"] = ndmo.DEFAULT_LEVEL
        data["confidence"] = min(_coerce_confidence(data.get("confidence"), 0.3), 0.4)
    else:
        data["ndmo_level"] = level
        data["confidence"] = _coerce_confidence(data.get("confidence"), 0.7)
    data.setdefault("impact_category", _IMPACT_BY_LEVEL.get(data["ndmo_level"], "أنشطة الجهات"))
    data.setdefault("impact_level", ndmo.IMPACT_OF_LEVEL[data["ndmo_level"]])
    data.setdefault("evidence_span", "")
    data.setdefault("rationale_ar", "")
    data["source"] = "allam"
    return data


def keyword_signal(content: str) -> dict:
    """Always-on deterministic keyword pass, independent of Ollama.

    Layer 2 (the 7B model) reliably under-calls «سري للغاية» — it recognises the
    national-security wording but settles one level down on «سري». This pass is
    kept as a cheap, explainable safety net for that single level; the policy
    layer decides how much authority to give it.
    """
    return _heuristic(content)


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
