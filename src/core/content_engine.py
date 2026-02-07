# FILE: src/core/content_engine.py
from __future__ import annotations

import json
from typing import Any

from core.validation import validate_part1, validate_part2, validate_analysis, validate_gate
from core.fallback_content import fallback_part1, fallback_part2, fallback_analysis, fallback_gate
from integrations.llm_client import LLMClient

SYSTEM_RULES = (
    "You are the content engine for Career Quest Map. "
    "Return valid JSON only. No extra text. "
    "Keep strings short and safe for a Pygame UI. "
    "Do not invent precise statistics. Use safe ranges or qualitative wording. "
)


def _json_schema_hint_part1() -> str:
    return (
        "Schema A JSON:\n"
        "{\n"
        '  "questions": [\n'
        "    {\"id\":\"...\",\"type\":\"mcq\",\"prompt\":\"...\",\"options\":[\"...\",\"...\"]},\n"
        "    {\"id\":\"...\",\"type\":\"slider\",\"prompt\":\"...\",\"scale\":{\"min\":0,\"max\":10,\"min_label\":\"...\",\"max_label\":\"...\"}},\n"
        "    {\"id\":\"...\",\"type\":\"rating\",\"prompt\":\"...\",\"scale\":{\"min\":1,\"max\":5}},\n"
        "    {\"id\":\"...\",\"type\":\"text\",\"prompt\":\"...\",\"placeholder\":\"...\"}\n"
        "  ]\n"
        "}\n"
        "Rules: Exactly 5 questions. Mix types."
    )


def _json_schema_hint_part2(is_poly: bool) -> str:
    extra = (
        "\"poly_extra_question\": {\"id\":\"poly_path\",\"type\":\"mcq\",\"prompt\":\"...\",\"options\":[\"Work\",\"Go to uni\"]}"
        if is_poly else
        "\"poly_extra_question\": null"
    )
    return (
        "Schema B JSON:\n"
        "{\n"
        '  "inferred_fields": [\"field1\",\"field2\",\"field3\"],\n'
        '  "questions": [ /* 12 items, same question schema as Part 1 */ ],\n'
        f"  {extra}\n"
        "}\n"
        "Rules: Exactly 3 fields and 12 questions. Questions must relate to the 3 fields."
    )


def _json_schema_hint_analysis(options_kind: str) -> str:
    return (
        "Schema C JSON:\n"
        "{\n"
        '  "strength_tags": [\"...\" x5],\n'
        '  "work_style_tags": [\"...\" x3..6],\n'
        '  "feedback_lines": [\"...\" x2..5],\n'
        '  "suggested_options": [\"...\",\"...\",\"...\"]\n'
        "}\n"
        f"Rules: suggested_options must be {options_kind}."
    )


def _json_schema_hint_gate(work_path: bool) -> str:
    extra = ""
    if work_path:
        extra = ', "salary_outlook_line":"...", "work_style_line":"..."'
    return (
        "Schema D JSON:\n"
        "{\n"
        '  "info_dialog_lines": [\"...\"],\n'
        f'  "dragon": {{"micro_quest_1_week":"...","mini_project_1_month":"...","resources":["..."]}}{extra}\n'
        "}\n"
        "Rules: info_dialog_lines must mention subjects to study, outlook in safe wording, impact on people."
    )


class ContentEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def gen_part1(self, education_status: str, poly_course: str | None) -> dict[str, Any]:
        if not self.llm.enabled:
            out = fallback_part1(education_status)
            validate_part1(out)
            return out

        user_prompt = (
            "Generate Part 1 questions.\n"
            f"education_status: {education_status}\n"
            f"poly_course_of_study: {poly_course or ''}\n"
            f"{_json_schema_hint_part1()}"
        )
        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        validate_part1(out)
        return out

    def gen_part2(self, education_status: str, part1_answers: list[Any]) -> dict[str, Any]:
        is_poly = education_status == "Poly"
        if not self.llm.enabled:
            out = fallback_part2(education_status, part1_answers)
            validate_part2(out, is_poly=is_poly)
            return out

        user_prompt = (
            "Infer 3 fields from Part 1 answers and generate Part 2 questions.\n"
            f"education_status: {education_status}\n"
            f"part1_answers_json: {json.dumps(part1_answers, ensure_ascii=False)}\n"
            f"{_json_schema_hint_part2(is_poly=is_poly)}"
        )
        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        validate_part2(out, is_poly=is_poly)
        return out

    def gen_analysis(
        self,
        education_status: str,
        poly_path_choice: str | None,
        inferred_fields: list[str],
        part2_answers: list[Any],
    ) -> dict[str, Any]:
        options_kind = "careers" if (
            education_status == "Poly" and poly_path_choice == "Work") else "courses"
        if not self.llm.enabled:
            out = fallback_analysis(
                education_status, poly_path_choice, inferred_fields, part2_answers)
            validate_analysis(out, options_kind=options_kind)
            return out

        user_prompt = (
            "Produce analysis and 3 suggested options.\n"
            f"education_status: {education_status}\n"
            f"poly_path_choice: {poly_path_choice or ''}\n"
            f"inferred_fields: {json.dumps(inferred_fields, ensure_ascii=False)}\n"
            f"part2_answers_json: {json.dumps(part2_answers, ensure_ascii=False)}\n"
            f"{_json_schema_hint_analysis(options_kind)}"
        )
        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        validate_analysis(out, options_kind=options_kind)
        return out

    def gen_gate_scene(self, option_name: str, work_path: bool) -> dict[str, Any]:
        if not self.llm.enabled:
            out = fallback_gate(option_name, work_path)
            validate_gate(out, need_salary=work_path)
            return out

        user_prompt = (
            "Generate gate scene content.\n"
            f"option_name: {option_name}\n"
            f"work_path: {work_path}\n"
            f"{_json_schema_hint_gate(work_path)}"
        )
        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        validate_gate(out, need_salary=work_path)
        return out
