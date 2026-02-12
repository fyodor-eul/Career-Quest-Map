from __future__ import annotations

import json
from typing import Any, Dict, List

from app.config import AppConfig
from app.state import AppState
from core.content_engine import ContentEngine
from integrations.llm_client import LLMClient


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
    placeholder = q.get("placeholder", "")
    if not isinstance(placeholder, str):
        placeholder = ""
    return {
        "type": "textinput",
        "question": prompt,
        "placeholder": placeholder,
        "user_input": "",
    }


def _convert_payload_for_ui(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    qs = payload.get("questions", [])
    items: List[Dict[str, Any]] = []
    if isinstance(qs, list):
        for q in qs:
            if isinstance(q, dict):
                items.append(_convert_question_for_ui(q))
    peq = payload.get("poly_extra_question")
    if isinstance(peq, dict):
        items.append(_convert_question_for_ui(peq))
    return items


def _mock_answer_for_question(q: Dict[str, Any]) -> Any:
    qtype = q.get("type")
    if qtype == "mcq":
        opts = q.get("options", [])
        if isinstance(opts, list) and opts:
            return opts[0]
        return ""
    if qtype == "slider":
        scale = q.get("scale", {})
        mn, mx = 0, 10
        if isinstance(scale, dict):
            if isinstance(scale.get("min"), (int, float)):
                mn = int(scale.get("min"))
            if isinstance(scale.get("max"), (int, float)):
                mx = int(scale.get("max"))
        return (mn + mx) // 2
    if qtype == "rating":
        return 3
    if qtype == "text":
        return "Sample answer"
    return ""


def _mock_answers_from_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    answers: List[Dict[str, Any]] = []
    qs = payload.get("questions", [])
    if isinstance(qs, list):
        for q in qs:
            if not isinstance(q, dict):
                continue
            answers.append({
                "id": q.get("id"),
                "type": q.get("type"),
                "prompt": q.get("prompt"),
                "answer": _mock_answer_for_question(q),
            })
    peq = payload.get("poly_extra_question")
    if isinstance(peq, dict):
        answers.append({
            "id": peq.get("id"),
            "type": peq.get("type"),
            "prompt": peq.get("prompt"),
            "answer": _mock_answer_for_question(peq),
        })
    return answers


def main() -> None:
    cfg = AppConfig()
    llm = LLMClient(
        cfg.azure_endpoint,
        cfg.azure_api_key,
        cfg.azure_api_version,
        cfg.azure_deployment,
    )
    engine = ContentEngine(llm)

    education_status = "Poly"
    poly_course = "IT"

    part1_payload = engine.gen_part1(education_status, poly_course)
    part1_ui = _convert_payload_for_ui(part1_payload)
    print("Part 1 UI questions:")
    print(json.dumps(part1_ui, ensure_ascii=False, indent=2))

    # Mock answers for part 1 to drive part 2
    part1_answers = _mock_answers_from_payload(part1_payload)
    part2_payload = engine.gen_part2(education_status, part1_answers)
    part2_ui = _convert_payload_for_ui(part2_payload)
    print("\nPart 2 UI questions:")
    print(json.dumps(part2_ui, ensure_ascii=False, indent=2))

    # Mock answers for part 2 to drive analysis
    part2_answers = _mock_answers_from_payload(part2_payload)
    inferred_fields = part2_payload.get("inferred_fields", [])
    poly_path_choice = "Work" if education_status == "Poly" else None

    analysis = engine.gen_analysis(
        education_status=education_status,
        poly_path_choice=poly_path_choice,
        inferred_fields=inferred_fields if isinstance(inferred_fields, list) else [],
        part2_answers=part2_answers,
    )
    print("\nAnalysis output:")
    print(json.dumps(analysis, ensure_ascii=False, indent=2))

    suggested = analysis.get("suggested_options", [])
    if isinstance(suggested, list) and suggested:
        option_name = str(suggested[2])
        work_path = bool(education_status == "Poly" and poly_path_choice == "Work")
        gate = engine.gen_gate_scene(
            option_name=option_name,
            work_path=work_path,
            education_status=education_status,
            poly_path_choice=poly_path_choice,
        )
        print("\nGate scene output:")
        print(json.dumps(gate, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
