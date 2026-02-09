from __future__ import annotations
from typing import Any


def _is_str_list(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _validate_question(q: Any) -> None:
    if not isinstance(q, dict):
        raise ValueError("question: must be dict")
    if q.get("type") not in ("mcq", "slider", "rating", "text"):
        raise ValueError("question: invalid type")
    if not isinstance(q.get("id"), str) or not isinstance(q.get("prompt"), str):
        raise ValueError("question: id and prompt required")
    t = q["type"]
    if t == "mcq":
        if not _is_str_list(q.get("options")) or len(q["options"]) < 2:
            raise ValueError("question: mcq needs options")
    if t == "slider":
        s = q.get("scale")
        if not isinstance(s, dict):
            raise ValueError("question: slider needs scale dict")
        for k in ("min", "max", "min_label", "max_label"):
            if k not in s:
                raise ValueError("question: slider scale missing field")
    if t == "rating":
        s = q.get("scale")
        if s != {"min": 1, "max": 5}:
            raise ValueError("question: rating scale must be 1-5")
    if t == "text":
        if not isinstance(q.get("placeholder"), str):
            raise ValueError("question: text needs placeholder")


def validate_part1(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("part1: payload must be dict")
    qs = payload.get("questions")
    if not isinstance(qs, list) or len(qs) != 5:
        raise ValueError("part1: questions must be list of 5")
    for q in qs:
        _validate_question(q)


def validate_part2(payload: dict[str, Any], is_poly: bool) -> None:
    if not isinstance(payload, dict):
        raise ValueError("part2: payload must be dict")
    fields = payload.get("inferred_fields")
    if not _is_str_list(fields) or len(fields) != 3:
        raise ValueError("part2: inferred_fields must be 3 strings")
    qs = payload.get("questions")
    if not isinstance(qs, list) or len(qs) != 12:
        raise ValueError("part2: questions must be list of 12")
    for q in qs:
        _validate_question(q)
    if is_poly:
        peq = payload.get("poly_extra_question")
        if not isinstance(peq, dict):
            raise ValueError(
                "part2: poly_extra_question must be dict for Poly")
        _validate_question(peq)
        opts = peq.get("options")
        if opts != ["Work", "Go to uni"]:
            raise ValueError(
                "part2: poly_extra_question options must be ['Work','Go to uni']")
    else:
        if payload.get("poly_extra_question") is not None:
            raise ValueError(
                "part2: poly_extra_question must be null for non-Poly")


def validate_analysis(payload: dict[str, Any], options_kind: str) -> None:
    st = payload.get("strength_tags")
    ws = payload.get("work_style_tags")
    fb = payload.get("feedback_lines")
    so = payload.get("suggested_options")
    if not _is_str_list(st) or len(st) != 5:
        raise ValueError("analysis: strength_tags must be 5 strings")
    if not _is_str_list(ws) or not (3 <= len(ws) <= 6):
        raise ValueError("analysis: work_style_tags must be 3-6 strings")
    if not _is_str_list(fb) or not (2 <= len(fb) <= 5):
        raise ValueError("analysis: feedback_lines must be 2-5 strings")
    if not _is_str_list(so) or len(so) != 3:
        raise ValueError("analysis: suggested_options must be 3 strings")
    if options_kind not in ("courses", "careers"):
        raise ValueError("analysis: options_kind invalid")


def validate_gate(payload: dict[str, Any], need_salary: bool) -> None:
    info = payload.get("info_dialog_lines")
    if not _is_str_list(info) or len(info) < 3:
        raise ValueError("gate: info_dialog_lines must be list[str] >= 3")
    if need_salary:
        if not isinstance(payload.get("salary_outlook_line"), str):
            raise ValueError(
                "gate: salary_outlook_line required for Work path")
        if not isinstance(payload.get("work_style_line"), str):
            raise ValueError("gate: work_style_line required for Work path")
    dq = payload.get("dragon")
    if not isinstance(dq, dict):
        raise ValueError("gate: dragon must be dict")
    for k in ("micro_quest_1_week", "mini_project_1_month"):
        if not isinstance(dq.get(k), str):
            raise ValueError("gate: dragon quest missing")
    res = dq.get("resources")
    if not _is_str_list(res) or len(res) < 2:
        raise ValueError("gate: dragon resources must be list[str] >= 2")
