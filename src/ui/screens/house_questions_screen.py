from __future__ import annotations

import time
from typing import Any, Optional

import pygame

from ui.widgets import Button
from ui.screen_manager import ScreenManager
from app.state import AppState


class HouseQuestionsScreen:
    """
    Minimal Part 1 runner.
    - Reads state.part1_payload
    - Shows questions one by one
    - Collects answers (simple text for now)
    - Calls back to TrainingMapScreen.on_part1_completed(...)
    """

    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int, back_screen):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height
        self.back_screen = back_screen

        self.font_title = pygame.font.Font(None, 40)
        self.font = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 22)

        payload = getattr(self.state, "part1_payload", {"questions": []})
        self.questions = payload.get(
            "questions", []) if isinstance(payload, dict) else []
        self.idx = 0

        self.input_text = ""
        self.input_active = True

        self.btn_next = Button(pygame.Rect(
            self.w - 200, self.h - 90, 160, 50), "Next", pygame.font.Font(None, 32))
        self.btn_back = Button(pygame.Rect(
            40, self.h - 90, 160, 50), "Back", pygame.font.Font(None, 32))

        self.answers: list[dict[str, Any]] = []

        self.toast: Optional[str] = None
        self.toast_until = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.btn_next.handle_mouse(event.pos)
            self.btn_back.handle_mouse(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.clicked(event.pos):
                self.sm.set(self.back_screen)
                return
            if self.btn_next.clicked(event.pos):
                self._commit_and_next()
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._commit_and_next()
                return
            if event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return

            if event.unicode and len(event.unicode) == 1 and len(self.input_text) < 80:
                if ord(event.unicode) >= 32:
                    self.input_text += event.unicode

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((245, 245, 250))

        title = self.font_title.render(
            "Part 1: House Questions", True, (25, 25, 35))
        surface.blit(title, (self.w // 2 - title.get_width() // 2, 40))

        if not self.questions:
            msg = self.font.render(
                "No questions found in state.part1_payload.", True, (60, 60, 80))
            surface.blit(msg, (60, 140))
            self.btn_back.draw(surface)
            return

        q = self.questions[self.idx]
        prompt = str(q.get("prompt", ""))
        qtype = str(q.get("type", "text"))
        qid = str(q.get("id", f"q{self.idx+1}"))

        meta = self.font_small.render(
            f"{self.idx+1}/{len(self.questions)}   id={qid}   type={qtype}", True, (90, 90, 110))
        surface.blit(meta, (60, 110))

        prompt_lines = self._wrap(prompt, 60)
        y = 150
        for line in prompt_lines:
            s = self.font.render(line, True, (40, 40, 55))
            surface.blit(s, (60, y))
            y += 30

        # Show options if MCQ
        if qtype == "mcq":
            opts = q.get("options", [])
            if isinstance(opts, list):
                y += 10
                for i, opt in enumerate(opts[:6]):
                    line = f"{i+1}) {opt}"
                    s = self.font_small.render(line, True, (50, 50, 70))
                    surface.blit(s, (80, y))
                    y += 24

        # Simple answer box (text for now, even for sliders/ratings)
        y += 20
        box = pygame.Rect(60, y, self.w - 120, 44)
        pygame.draw.rect(surface, (255, 255, 255), box, border_radius=10)
        pygame.draw.rect(surface, (180, 180, 200), box, 2, border_radius=10)

        ans = self.input_text if self.input_text else "Type your answer here, press Enter"
        color = (40, 40, 55) if self.input_text else (140, 140, 160)
        surface.blit(self.font.render(ans, True, color),
                     (box.x + 12, box.y + 10))

        self.btn_back.draw(surface)
        self.btn_next.draw(surface)

        if self.toast and time.time() < self.toast_until:
            self._draw_toast(surface, self.toast)

    def _commit_and_next(self) -> None:
        if not self.questions:
            return

        q = self.questions[self.idx]
        entry = {
            "id": q.get("id", f"q{self.idx+1}"),
            "type": q.get("type", "text"),
            "prompt": q.get("prompt", ""),
            "answer": self.input_text.strip(),
        }
        self.answers.append(entry)
        self.input_text = ""

        if self.idx < len(self.questions) - 1:
            self.idx += 1
            return

        # Done Part 1
        try:
            self.back_screen.on_part1_completed(self.answers)
        except Exception:
            pass

        self.sm.set(self.back_screen)

    def _wrap(self, text: str, max_chars: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        line: list[str] = []
        count = 0
        for w in words:
            add = len(w) + (1 if line else 0)
            if count + add <= max_chars:
                line.append(w)
                count += add
            else:
                lines.append(" ".join(line))
                line = [w]
                count = len(w)
        if line:
            lines.append(" ".join(line))
        return lines

    def _draw_toast(self, surface: pygame.Surface, text: str) -> None:
        padding = 10
        surf = self.font_small.render(text, True, (255, 255, 255))
        w = surf.get_width() + padding * 2
        h = surf.get_height() + padding * 2
        x = (self.w - w) // 2
        y = self.h - h - 16
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (20, 20, 30), rect, border_radius=10)
        surface.blit(surf, (x + padding, y + padding))
