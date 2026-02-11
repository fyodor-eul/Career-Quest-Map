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
    part1_answers = [{"id": q.get("id"), "answer": ""} for q in part1_payload.get("questions", [])]

    part2_payload = engine.gen_part2(education_status, part1_answers)
    part2_ui = _convert_payload_for_ui(part2_payload)
    print("\nPart 2 UI questions:")
    print(json.dumps(part2_ui, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
