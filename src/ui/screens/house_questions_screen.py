from __future__ import annotations

import time
from typing import Any, Optional

import pygame

from ui.widgets import Button
from ui.screens.question_modal import QuestionModal
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

        self.modal = QuestionModal(self.w, self.h)

        self.btn_next = Button(pygame.Rect(
            self.w - 200, self.h - 90, 160, 50), "Next", pygame.font.Font(None, 32))
        self.btn_back = Button(pygame.Rect(
            40, self.h - 90, 160, 50), "Back", pygame.font.Font(None, 32))

        self.answers: list[dict[str, Any]] = []

        self.toast: Optional[str] = None
        self.toast_until = 0.0

        if self.questions:
            self._open_current()

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

        self.modal.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.modal.active and self.modal.done:
                self._commit_and_next()
            return

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

        self.btn_back.draw(surface)
        self.btn_next.draw(surface)

        if self.toast and time.time() < self.toast_until:
            self._draw_toast(surface, self.toast)
        elif self.toast and time.time() >= self.toast_until:
            self.toast = None

        self.modal.draw(surface)

    def _commit_and_next(self) -> None:
        if not self.questions:
            return

        if not self.modal.done:
            self._toast("Answer the question first.", seconds=1.5)
            return

        q = self.questions[self.idx]
        entry = {
            "id": q.get("id", f"q{self.idx+1}"),
            "type": q.get("type", "text"),
            "prompt": q.get("prompt", ""),
            "answer": self.modal.answer,
        }
        self.answers.append(entry)
        self.modal.active = False

        if self.idx < len(self.questions) - 1:
            self.idx += 1
            self._open_current()
            return

        # Done Part 1
        try:
            self.back_screen.on_part1_completed(self.answers)
        except Exception:
            pass

        self.sm.set(self.back_screen)

    def _open_current(self) -> None:
        if not self.questions:
            return
        q = self.questions[self.idx]
        if isinstance(q, dict) and q.get("type") in ("mcq", "slider", "rating", "text"):
            self.modal.open(q)

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
