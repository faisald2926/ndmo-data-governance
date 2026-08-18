"""Orchestrates the 3-layer hybrid classifier: rules -> LLM -> policy."""
from . import llm, policy, rules

# Only invoke the LLM when there is enough free text to reason about.
_MIN_TEXT_LEN = 12


def classify_record(content: dict | None = None, text: str = "") -> dict:
    """Classify one record. `content` is a structured row dict; `text` is the
    free-text blob (for citizen requests / documents). Either may be empty.
    """
    content = content or {}
    text = (text or "").strip()

    rule_result = rules.classify(content, text)

    llm_result = keyword_result = None
    # Call the LLM for free-text rows, or when rules found nothing to anchor on.
    if len(text) >= _MIN_TEXT_LEN or rule_result.get("level") is None:
        llm_input = text if len(text) >= _MIN_TEXT_LEN else _row_to_text(content)
        if llm_input:
            llm_result = llm.classify_text(llm_input)
            # Deterministic and free — always available as a third signal.
            keyword_result = llm.keyword_signal(llm_input)

    return policy.decide(rule_result, llm_result, keyword_result)


def _row_to_text(content: dict) -> str:
    """Serialise a structured row into a short text for the LLM when needed."""
    parts = [f"{k}: {v}" for k, v in content.items() if v not in (None, "")]
    return " | ".join(parts)[:600]
