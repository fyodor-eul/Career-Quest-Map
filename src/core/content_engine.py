# FILE: src/core/content_engine.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from core.validation import (
    validate_part1,
    validate_part2,
    validate_analysis,
    validate_gate,
)
from core.fallback_content import (
    fallback_part1,
    fallback_part2,
    fallback_analysis,
    fallback_gate,
)
from integrations.llm_client import LLMClient


# ------------------------------------------------------------
# System rules (shared)
# ------------------------------------------------------------
SYSTEM_RULES = (
    "You are the content engine for a game-like career guidance application called 'Career Quest Map'. "
    "Return valid JSON only. Do not include any extra text, markdown, comments, or code fences. "
    "All strings must be safe for a Pygame UI: avoid emojis, avoid newlines inside strings, avoid tabs, keep concise. "
    "Do not invent precise real-world statistics. If asked about salary/employment, use safe ranges or qualitative phrasing. "
    "Follow the requested schema exactly and obey counts and constraints."
)


# ------------------------------------------------------------
# Prompt template helpers
# ------------------------------------------------------------
def _compact_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _build_prompt(task: str, context_lines: List[str], schema_hint: str, hard_rules: List[str]) -> str:
    """
    Consistent prompt template.
    """
    ctx = "\n".join(context_lines).strip()
    rules = "\n".join([f"- {r}" for r in hard_rules]).strip()
    return (
        f"Task:\n{task}\n\n"
        f"Context:\n{ctx}\n\n"
        f"Hard rules:\n{rules}\n\n"
        f"Schema:\n{schema_hint}\n"
    )


# ------------------------------------------------------------
# Schema hints
# ------------------------------------------------------------
def _schema_question() -> str:
    return (
        "Question schema (use only one per question depending on type):\n"
        "- MCQ:\n"
        '  {"id":"q1","type":"mcq","prompt":"...","options":["...","...","...","..."]}\n'
        "- Slider:\n"
        '  {"id":"q2","type":"slider","prompt":"...","scale":{"min":0,"max":10,"min_label":"...","max_label":"..."}}\n'
        "- Rating:\n"
        '  {"id":"q3","type":"rating","prompt":"...","scale":{"min":1,"max":5}}\n'
        "- Text:\n"
        '  {"id":"q4","type":"text","prompt":"...","placeholder":"..."}\n'
        "Notes:\n"
        "- Do not add extra keys.\n"
        "- Prompts must be sequential (q1..qN)."
    )


def _schema_part1() -> str:
    return (
        "Schema A JSON:\n"
        "{\n"
        '  "questions": [\n'
        "    /* exactly 5 questions following the Question schema */\n"
        "  ]\n"
        "}\n\n"
        f"{_schema_question()}"
    )


def _schema_part2(is_poly: bool) -> str:
    extra = (
        '"poly_extra_question":{"id":"poly_path","type":"mcq","prompt":"...","options":["Work","Go to uni"]}'
        if is_poly
        else '"poly_extra_question":null'
    )
    return (
        "Schema B JSON:\n"
        "{\n"
        '  "inferred_fields": ["field1","field2","field3"],\n'
        '  "questions": [\n'
        "    /* exactly 12 questions following the Question schema */\n"
        "  ],\n"
        f"  {extra}\n"
        "}\n\n"
        f"{_schema_question()}"
    )


def _schema_analysis(options_kind: str) -> str:
    return (
        "Schema C JSON:\n"
        "{\n"
        '  "strength_tags": ["...","...","...","...","..."],\n'
        '  "work_style_tags": ["...","...","..."],\n'
        '  "feedback_lines": ["...","..."],\n'
        '  "suggested_options": ["...","...","..."]\n'
        "}\n"
        "Rules:\n"
        "- strength_tags: exactly 5 items\n"
        "- work_style_tags: 3 to 6 items\n"
        "- feedback_lines: 2 to 5 lines\n"
        "- suggested_options: exactly 3\n"
        f"- suggested_options must be {options_kind} (specific names, not generic categories)"
    )


def _schema_gate(work_path: bool) -> str:
    # When work_path=True, include salary_outlook_line + work_style_line.
    if work_path:
        return (
            "Schema D JSON:\n"
            "{\n"
            '  "info_dialog_lines": ["..."],\n'
            '  "work_style_line": "...",\n'
            '  "salary_outlook_line": "...",\n'
            '  "dragon": {\n'
            '    "micro_quest_1_week": "...",\n'
            '    "mini_project_1_month": "...",\n'
            '    "resources": ["...","...","..."]\n'
            "  }\n"
            "}\n"
            "Rules:\n"
            "- info_dialog_lines must include: subjects to study, employment outlook in safe wording, impact on people\n"
            "- work_style_line must describe typical work style in that industry\n"
            "- salary_outlook_line must be a safe range or qualitative phrasing for a poly fresh graduate"
        )
    return (
        "Schema D JSON:\n"
        "{\n"
        '  "info_dialog_lines": ["..."],\n'
        '  "dragon": {\n'
        '    "micro_quest_1_week": "...",\n'
        '    "mini_project_1_month": "...",\n'
        '    "resources": ["...","...","..."]\n'
        "  }\n"
        "}\n"
        "Rules:\n"
        "- info_dialog_lines must include: subjects to study, employment outlook in safe wording, impact on people"
    )


# ------------------------------------------------------------
# Deterministic question type distribution
# ------------------------------------------------------------
PART1_DISTRIBUTION = ["mcq", "mcq", "slider", "rating", "text"]
PART2_DISTRIBUTION = [
    "mcq",
    "mcq",
    "mcq",
    "mcq",
    "slider",
    "slider",
    "slider",
    "rating",
    "rating",
    "rating",
    "text",
    "text",
]


def _dist_rules(distribution: List[str], start: int = 1) -> List[str]:
    """
    Returns hard rules forcing distribution and sequential IDs.
    """
    rules: List[str] = []
    for i, t in enumerate(distribution, start=start):
        rules.append(f'Question id "q{i}" must be type "{t}".')
    rules.append("Question IDs must be sequential and unique (q1..qN).")
    rules.append("Keep each prompt concise and single-line.")
    rules.append("For questions: MCQ options must be 4 options (short).")
    return rules


def _convert_question_for_ui(q: Dict[str, Any]) -> Dict[str, Any]:
    t = q.get("type")
    prompt = q.get("prompt", "")
    if t == "mcq":
        opts = q.get("options", [])
        if not isinstance(opts, list):
            opts = []
        return {
            "type": "multiple_choice",
            "select_count": len(opts),
            "question": prompt,
            "answers": opts,
            "user_choice_index": 0,
        }
    if t == "slider":
        scale = q.get("scale", {})
        mx = 10
        if isinstance(scale, dict) and isinstance(scale.get("max"), (int, float)):
            mx = int(scale.get("max"))
        return {
            "type": "slider",
            "select_count": mx,
            "question": prompt,
            "user_choice_index": 0,
        }
    if t == "rating":
        return {
            "type": "slider",
            "select_count": 5,
            "question": prompt,
            "user_choice_index": 0,
        }
    # text or fallback
    placeholder = q.get("placeholder", "")
    if not isinstance(placeholder, str):
        placeholder = ""
    return {
        "type": "textinput",
        "question": prompt,
        "placeholder": placeholder,
        "user_input": "",
    }


def _print_questions(tag: str, payload: Dict[str, Any]) -> None:
    qs = payload.get("questions") if isinstance(payload, dict) else None
    if not isinstance(qs, list):
        print(f"[{tag}] No questions to print.")
        return
    items: List[Dict[str, Any]] = []
    for q in qs:
        if isinstance(q, dict):
            items.append(_convert_question_for_ui(q))
    # Include poly extra question if present
    peq = payload.get("poly_extra_question") if isinstance(payload, dict) else None
    if isinstance(peq, dict):
        items.append(_convert_question_for_ui(peq))
    print(f"[{tag}] ui_questions = {json.dumps(items, ensure_ascii=False, indent=2)}")
    return {json.dumps(items, ensure_ascii=False, indent=2)}


# ------------------------------------------------------------
# Content Engine
# ------------------------------------------------------------
class ContentEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    # ---------------- Part 1 ----------------
    def gen_part1(self, education_status: str, poly_course: Optional[str]) -> Dict[str, Any]:
        """
        Schema A:
        - Exactly 5 questions
        - Enforced types: 2 mcq, 1 slider, 1 rating, 1 text
        - Poly vs non-Poly topic focus
        """
        if not getattr(self.llm, "enabled", False):
            out = fallback_part1(education_status)
            validate_part1(out)
            return out

        task = "Generate Part 1: exactly 5 sequential questions for the House."
        context_lines = [
            f"education_status: {education_status}",
            f"poly_course_of_study: {poly_course or ''}",
            "Part 1 topic focus:",
            "- If Secondary School or JC: general career curiosity, interests, passions, personality, preferred activities.",
            "- If Poly: difficulty with current course, frustrations, other passions/interests, motivation, preferred learning style.",
        ]

        hard_rules = [
            "Output JSON only.",
            "Exactly 5 questions.",
            "Questions must be sequential and feel like a natural progression (broad -> specific).",
            "Do not repeat the same theme twice.",
            "Do not mention brand names, paid-only tools, or sensitive personal data.",
            *(_dist_rules(PART1_DISTRIBUTION, start=1)),
            "For slider: scale min=0 max=10 and provide meaningful min_label and max_label.",
            "For rating: scale min=1 max=5.",
            "For text: include a short placeholder.",
        ]

        user_prompt = _build_prompt(task, context_lines, _schema_part1(), hard_rules)

        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        validate_part1(out)
        p1_q = _print_questions("Part1", out)
        return out

    # ---------------- Part 2 ----------------
    def gen_part2(self, education_status: str, part1_answers: List[Any]) -> Dict[str, Any]:
        """
        Schema B:
        - Infer exactly 3 fields
        - Generate exactly 12 questions
        - Enforced types: 4 mcq, 3 slider, 3 rating, 2 text
        - Poly: include poly_extra_question, else null
        """
        is_poly = education_status == "Poly"

        if not getattr(self.llm, "enabled", False):
            out = fallback_part2(education_status, part1_answers)
            validate_part2(out, is_poly=is_poly)
            return out

        task = "Generate Part 2: infer 3 potential fields and ask 12 sequential narrowing questions for the Wise Man."
        context_lines = [
            f"education_status: {education_status}",
            f"part1_answers_json: {_compact_json(part1_answers)}",
            "Inference requirement:",
            "- Use Part 1 answers to infer exactly 3 potential fields of interest.",
            "- Then ask 12 questions that narrow among those fields.",
            "Question strategy:",
            "- Early questions compare fields; later questions go deeper into preferences, strengths, and day-to-day tasks.",
        ]

        hard_rules = [
            "Output JSON only.",
            "inferred_fields must contain exactly 3 distinct fields, each 1-3 words (e.g., 'Software', 'Design', 'Business').",
            "questions must contain exactly 12 questions.",
            "All 12 questions must relate to the inferred fields and help narrow interest.",
            "Keep questions appropriate to the user's education level.",
            "Do not include real statistics. Keep any outlook language qualitative.",
            *(_dist_rules(PART2_DISTRIBUTION, start=1)),
            "For slider: scale min=0 max=10 and provide meaningful labels.",
            "For rating: scale min=1 max=5.",
            "For text: include a short placeholder.",
            ("If education_status is Poly: poly_extra_question must be present as an MCQ with options Work and Go to uni."
             if is_poly else
             "If education_status is not Poly: poly_extra_question must be null."),
            "poly_extra_question options must be exactly: [\"Work\",\"Go to uni\"] (2 options).",
        ]

        user_prompt = _build_prompt(task, context_lines, _schema_part2(is_poly=is_poly), hard_rules)

        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        try:
            validate_part2(out, is_poly=is_poly)
            fields = out.get("inferred_fields", [])
            if isinstance(fields, list):
                print(f"[Part2] inferred_fields: {fields}")
            _print_questions("Part2", out)
            return out
        except Exception:
            fallback = fallback_part2(education_status, part1_answers)
            validate_part2(fallback, is_poly=is_poly)
            return fallback

    # ---------------- Analysis ----------------
    def gen_analysis(
        self,
        education_status: str,
        poly_path_choice: Optional[str],
        inferred_fields: List[str],
        part2_answers: List[Any],
    ) -> Dict[str, Any]:
        """
        Schema C:
        - 5 strength tags
        - 3-6 work style tags
        - 2-5 feedback lines (fantasy-lite, short)
        - exactly 3 suggested options:
            - Poly Work -> careers/roles
            - Else -> courses
        """
        options_kind = "careers" if (education_status == "Poly" and poly_path_choice == "Work") else "courses"

        if not getattr(self.llm, "enabled", False):
            out = fallback_analysis(education_status, poly_path_choice, inferred_fields, part2_answers)
            validate_analysis(out, options_kind=options_kind)
            return out

        task = "Produce analysis: strength tags, work style tags, short feedback lines, and 3 suggested options."
        context_lines = [
            f"education_status: {education_status}",
            f"poly_path_choice: {poly_path_choice or ''}",
            f"inferred_fields: {_compact_json(inferred_fields)}",
            f"part2_answers_json: {_compact_json(part2_answers)}",
            "Output tone:",
            "- Fantasy-lite, like a wise man advising a young explorer. Keep lines short.",
        ]

        hard_rules = [
            "Output JSON only.",
            "strength_tags: exactly 5 (use clear single-word or short-phrase tags).",
            "work_style_tags: 3 to 6 items.",
            "feedback_lines: 2 to 5 short lines.",
            "suggested_options: exactly 3.",
            (f"suggested_options must be specific {options_kind}. "
             "For courses use names like 'Computer Engineering', 'Business Management'. "
             "For careers use roles like 'Junior Data Analyst', 'Mobile App Developer'."),
            "Do not output generic options like 'Engineering' or 'IT'. Be specific.",
            "Avoid precise statistics.",
        ]

        user_prompt = _build_prompt(task, context_lines, _schema_analysis(options_kind), hard_rules)

        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        validate_analysis(out, options_kind=options_kind)
        return out

    # ---------------- Gate Scene ----------------
    def gen_gate_scene(
        self,
        option_name: str,
        work_path: bool,
        education_status: Optional[str] = None,
        poly_path_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schema D:
        - info_dialog_lines include:
            - subjects to study
            - employment outlook (safe wording)
            - impact on people's lives
          If work_path=True:
            - include salary_outlook_line (safe range/qualitative for poly fresh grad)
            - include work_style_line
        - dragon quests feasible for Secondary/JC/Poly
        """
        if not getattr(self.llm, "enabled", False):
            out = fallback_gate(option_name, work_path)
            validate_gate(out, need_salary=work_path)
            return out

        edu = education_status or ""
        poly_choice = poly_path_choice or ""

        task = "Generate gate scene content for the chosen option."
        context_lines = [
            f"option_name: {option_name}",
            f"work_path: {work_path}",
            f"education_status: {edu}",
            f"poly_path_choice: {poly_choice}",
            "Scene requirements:",
            "- Wise man explains: subjects to study, employment outlook (safe wording), impact on people.",
            "- Then the player can choose Yes/No (UI handles this).",
            "- If Yes: dragon warrior provides a 1-week micro quest, 1-month mini project, and resources.",
            "Feasibility constraint:",
            "- Quests must be feasible for Secondary School, JC, and Poly students (no expensive equipment).",
            "Tone:",
            "- Fantasy-lite, short dialog lines.",
        ]

        hard_rules = [
            "Output JSON only.",
            "info_dialog_lines must be 3 to 7 short lines.",
            "info_dialog_lines must include: subjects to study, employment outlook in safe wording, impact on people.",
            "dragon.resources must be a list of 3 to 6 general resources (free/commonly accessible).",
            "Do not assume paid-only services.",
            "Do not include precise statistics.",
            "Micro quest: 1 week, 5-7 short sessions (<=60 min each) ending with a tangible output.",
            "Mini project: 1 month with 3 phases (Plan, Build, Review) ending with a showable deliverable.",
            "Mini project must use free tools and no expensive equipment.",
            "Resources must include exactly 4 items: official docs/reference, beginner tutorial/course, example project/template, community/forum.",
        ]
        if work_path:
            hard_rules.extend([
                "Include work_style_line (1 short line).",
                "Include salary_outlook_line using safe ranges or qualitative phrasing for a poly fresh graduate.",
                "Salary line must avoid exact single numbers; use ranges like 'around S$2.5k- S$3.2k' or qualitative phrasing.",
            ])

        user_prompt = _build_prompt(task, context_lines, _schema_gate(work_path), hard_rules)

        out = self.llm.invoke_json(SYSTEM_RULES, user_prompt)
        validate_gate(out, need_salary=work_path)
        return out
