"""Pydantic request/response models for the API."""
from typing import Any

from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    text: str | None = None
    content: dict[str, Any] | None = None

    model_config = {"json_schema_extra": {"examples": [
        {"text": "أعاني من حالة صحية وأطلب إعفاءً، هويتي 1043215789"},
        {"content": {"invoice_no": "INV-1", "payment_iban": "SA0380000000608010167519",
                     "subtotal": "1000"}},
    ]}}


class PipelineRequest(BaseModel):
    max_per_file: int | None = None
