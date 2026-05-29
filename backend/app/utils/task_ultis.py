"""Tiện ích task dùng chung — tách riêng để tránh circular import."""
from app.models.task import Task


def infer_priority(base_weight: int) -> str:
    if base_weight >= 4:
        return "High"
    if base_weight >= 2:
        return "Medium"
    return "Low"