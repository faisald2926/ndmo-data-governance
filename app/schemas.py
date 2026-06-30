"""Pydantic request/response models for the API."""
from typing import Any

from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    text: str | None = None
    content: dict[str, Any] | None = None


class PipelineRequest(BaseModel):
    max_per_file: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"


class RecordUpdate(BaseModel):
    ndmo_level: str | None = None
    needs_review: bool | None = None
