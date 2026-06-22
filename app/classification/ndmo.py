"""Shared NDMO vocabulary and policy constants (single source of truth)."""

# The four NDMO levels, lowest -> highest sensitivity.
PUBLIC = "عام"
RESTRICTED = "مقيّد"
SECRET = "سري"
TOP_SECRET = "سري للغاية"

LEVELS = [PUBLIC, RESTRICTED, SECRET, TOP_SECRET]
LEVEL_RANK = {lvl: i for i, lvl in enumerate(LEVELS)}

# Policy: anything that cannot be confidently classified is treated as Restricted.
DEFAULT_LEVEL = RESTRICTED

# Impact level that maps to each classification level (for display).
IMPACT_OF_LEVEL = {
    TOP_SECRET: "عالي",
    SECRET: "متوسط",
    RESTRICTED: "منخفض",
    PUBLIC: "لا يوجد",
}

IMPACT_CATEGORIES = [
    "المصلحة الوطنية",   # National interest
    "أنشطة الجهات",      # Entity activities
    "الأفراد",           # Individuals (health / privacy / IP)
    "البيئة",            # Environment
]

# Short control guidance per level (from the classification policy controls section).
CONTROLS = {
    TOP_SECRET: "تشفير معتمد، وصول مقيّد بمواقع محددة، حظر النسخ، تسجيل كامل للوصول.",
    SECRET: "تشفير أثناء التخزين والنقل، وصول وفق الحاجة للمعرفة، مراقبة الوصول.",
    RESTRICTED: "ضبط وصول وفق أقل امتياز، تشفير الحقول الحساسة، تسجيل الوصول.",
    PUBLIC: "لا قيود سرية؛ يمكن النشر كبيانات مفتوحة بعد المراجعة.",
}


def higher(a: str, b: str) -> str:
    """Return the higher-sensitivity of two levels (aggregation rule)."""
    if a not in LEVEL_RANK:
        return b
    if b not in LEVEL_RANK:
        return a
    return a if LEVEL_RANK[a] >= LEVEL_RANK[b] else b


def highest(levels) -> str:
    """Highest level across an iterable; defaults to PUBLIC if empty."""
    result = PUBLIC
    for lvl in levels:
        result = higher(result, lvl)
    return result
