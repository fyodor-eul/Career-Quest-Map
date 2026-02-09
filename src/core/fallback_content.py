from __future__ import annotations
from typing import Any


def fallback_part1(education_status: str) -> dict[str, Any]:
    if education_status == "Poly":
        qs = [
            {"id": "q1", "type": "rating",
                "prompt": "How manageable is your current course workload?", "scale": {"min": 1, "max": 5}},
            {"id": "q2", "type": "mcq", "prompt": "Which part frustrates you most right now?", "options": [
                "Concepts feel abstract", "Too much memorising", "Too fast pace", "Group work issues", "Not interested in modules"]},
            {"id": "q3", "type": "slider", "prompt": "How much do you enjoy hands-on work versus theory?",
                "scale": {"min": 0, "max": 10, "min_label": "More theory", "max_label": "More hands-on"}},
            {"id": "q4", "type": "text", "prompt": "Name 1 activity you enjoy even outside school.",
                "placeholder": "Example: editing videos, coding, sports"},
            {"id": "q5", "type": "mcq", "prompt": "When learning something new, you prefer:", "options": [
                "Step-by-step notes", "Try first, learn by doing", "Watch examples", "Discuss with people"]},
        ]
    else:
        qs = [
            {"id": "q1", "type": "mcq", "prompt": "Which school tasks do you enjoy most?", "options": [
                "Math/Logic", "Writing/Language", "Design/Art", "Science/Lab", "Helping people"]},
            {"id": "q2", "type": "slider", "prompt": "How much do you like working with people?", "scale": {
                "min": 0, "max": 10, "min_label": "Prefer solo", "max_label": "Prefer people"}},
            {"id": "q3", "type": "rating",
                "prompt": "How confident are you in solving problems under time pressure?", "scale": {"min": 1, "max": 5}},
            {"id": "q4", "type": "text", "prompt": "If you could learn any skill in 3 months, what would it be?",
                "placeholder": "Example: coding, baking, photography"},
            {"id": "q5", "type": "mcq", "prompt": "Pick the most accurate statement:", "options": [
                "I like clear structure", "I like flexibility", "I like creating things", "I like analysing patterns"]},
        ]
    return {"questions": qs}


def fallback_part2(education_status: str, part1_answers: list[Any]) -> dict[str, Any]:
    fields = ["Technology", "Business", "Design"]
    poly_extra = None
    if education_status == "Poly":
        poly_extra = {"id": "poly_path", "type": "mcq",
                      "prompt": "After poly, what is your plan?", "options": ["Work", "Go to uni"]}
    qs = []
    for i in range(12):
        qs.append({"id": f"q{i+1}", "type": "mcq", "prompt": f"Which sounds more interesting right now? (Q{i+1})",
                  "options": [f"{fields[i % 3]} option A", f"{fields[i % 3]} option B", f"{fields[i % 3]} option C"]})
    return {"inferred_fields": fields, "questions": qs, "poly_extra_question": poly_extra}


def fallback_analysis(education_status: str, poly_path_choice: str | None, inferred_fields: list[str], part2_answers: list[Any]) -> dict[str, Any]:
    strength = ["Analytical", "Creative",
                "Organized", "Empathetic", "Persuasive"]
    work_style = ["Team", "Structured", "Task-focused"]
    feedback = ["You show clear patterns in what you enjoy.",
                "Try small experiments before you commit.", "Use feedback from real projects to refine."]
    if education_status == "Poly" and poly_path_choice == "Work":
        options = ["Junior Data Analyst",
                   "Mobile App Developer", "Electronics Technician"]
    else:
        options = ["Computer Engineering",
                   "Business Management", "Digital Design"]
    return {
        "strength_tags": strength,
        "work_style_tags": work_style,
        "feedback_lines": feedback[:3],
        "suggested_options": options
    }


def fallback_gate(option_name: str, work_path: bool) -> dict[str, Any]:
    info = [
        f"For {option_name}, you will study core fundamentals plus applied skills.",
        "Employment outlook: generally stable. Your results depend on portfolio and internships.",
        "Impact: you can build solutions that help users, teams, or customers."
    ]
    payload: dict[str, Any] = {"info_dialog_lines": info}
    if work_path:
        payload["salary_outlook_line"] = "Fresh grad range: around low-to-mid $2k+, varies by role and company."
        payload["work_style_line"] = "Work style: mix of deadlines, collaboration, and independent problem-solving."
    payload["dragon"] = {
        "micro_quest_1_week": f"1-week micro quest: complete a short beginner tutorial related to {option_name} and write a 1-page reflection.",
        "mini_project_1_month": f"1-month mini project: build a small portfolio piece related to {option_name} and present it to a friend or mentor.",
        "resources": ["Official documentation basics", "YouTube beginner playlist", "Free online course intro", "Community forum Q&A"]
    }
    return payload
