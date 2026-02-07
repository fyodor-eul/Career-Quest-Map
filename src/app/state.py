from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

EducationStatus = Literal["Secondary School", "JC", "Poly"]
PolyPathChoice = Literal["Work", "Go to uni"]


@dataclass
class UserProfile:
    user_name: str = ""
    education_status: EducationStatus = "Secondary School"
    poly_course_of_study: str | None = None
    poly_path_choice: PolyPathChoice | None = None


@dataclass
class QAItem:
    qid: str
    qtype: Literal["mcq", "slider", "rating", "text"]
    prompt: str
    options: list[str] | None = None
    slider: dict[str, Any] | None = None
    placeholder: str | None = None


@dataclass
class GameData:
    part1_questions: list[QAItem] = field(default_factory=list)
    part1_answers: list[Any] = field(default_factory=list)

    inferred_fields: list[str] = field(default_factory=list)
    part2_questions: list[QAItem] = field(default_factory=list)
    part2_answers: list[Any] = field(default_factory=list)

    strength_tags: list[str] = field(default_factory=list)
    work_style_tags: list[str] = field(default_factory=list)
    feedback_lines: list[str] = field(default_factory=list)
    suggested_options: list[str] = field(default_factory=list)

    gates_log: list[dict[str, Any]] = field(default_factory=list)
    chosen_gate: str | None = None
    chosen_gate_yes: bool | None = None

    dragon_micro_quest: str | None = None
    dragon_mini_project: str | None = None
    dragon_resources: list[str] = field(default_factory=list)


@dataclass
class WorldState:
    # Scene progression
    # start, profile, training, part1, wise, gates, gate_scene, dragon_scene, end
    stage: str = "start"

    # Map flags
    part1_done: bool = False
    part2_done: bool = False

    # Player position for top-down scenes
    player_x: float = 120
    player_y: float = 260

    # House, wise man, gates zones
    house_entered: bool = False
    wise_met: bool = False


@dataclass
class AppState:
    profile: UserProfile = field(default_factory=UserProfile)
    data: GameData = field(default_factory=GameData)
    world: WorldState = field(default_factory=WorldState)
