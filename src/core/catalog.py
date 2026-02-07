# FILE: src/core/catalog.py
import json
import os
from typing import Any


def load_catalog(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("options_catalog.json must be a JSON object")
    return obj


def list_option_names(catalog: dict[str, Any], kind: str) -> list[str]:
    arr = catalog.get(kind, [])
    if not isinstance(arr, list):
        return []
    out: list[str] = []
    for item in arr:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            out.append(item["name"])
    return out


def find_option(catalog: dict[str, Any], kind: str, name: str) -> dict[str, Any] | None:
    arr = catalog.get(kind, [])
    if not isinstance(arr, list):
        return None
    for item in arr:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def simple_rank_top3(catalog: dict[str, Any], kind: str, inferred_fields: list[str]) -> list[str]:
    arr = catalog.get(kind, [])
    if not isinstance(arr, list):
        return []
    scored: list[tuple[int, str]] = []
    inf = set(inferred_fields)
    for item in arr:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        fields = item.get("fields", [])
        s = 0
        if isinstance(fields, list):
            s = len(inf.intersection(
                set([f for f in fields if isinstance(f, str)])))
        scored.append((s, item["name"]))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [name for _, name in scored[:3]]
