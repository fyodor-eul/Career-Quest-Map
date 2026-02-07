from __future__ import annotations
import json
import os
from datetime import datetime
from dataclasses import asdict
from app.state import AppState


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_run(state: AppState, out_dir: str) -> str:
    ensure_dir(out_dir)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"career_quest_map_run_{stamp}.txt")
    payload = asdict(state)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path
