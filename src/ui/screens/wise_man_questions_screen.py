from __future__ import annotations

from typing import Any
import pygame

from ui.widgets import Button
from ui.screens.question_modal import QuestionModal
from ui.screen_manager import ScreenManager
from app.state import AppState


class WiseManQuestionsScreen:
    """
    Minimal Part 2 runner.
    - Reads state.part2_payload
    - Shows 12 questions one by one
    - If poly_extra_question exists, ask it at the end
    - Collect answers as text for now
    - Calls back to TrainingMapScreen.on_part2_completed(...)
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

        payload = getattr(self.state, "part2_payload", {
                          "inferred_fields": [], "questions": [], "poly_extra_question": None})
        self.inferred_fields = payload.get(
            "inferred_fields", []) if isinstance(payload, dict) else []
        self.questions = payload.get(
            "questions", []) if isinstance(payload, dict) else []
        self.poly_extra = payload.get(
            "poly_extra_question", None) if isinstance(payload, dict) else None

        self.idx = 0

        self.asking_poly_extra = False
        self.poly_path_choice: str | None = None

        self.answers: list[dict[str, Any]] = []

        self.modal = QuestionModal(self.w, self.h)

        self.btn_next = Button(pygame.Rect(
            self.w - 200, self.h - 90, 160, 50), "Next", pygame.font.Font(None, 32))
        self.btn_back = Button(pygame.Rect(
            40, self.h - 90, 160, 50), "Back", pygame.font.Font(None, 32))

        if self.questions:
            self._open_current()
        elif self.poly_extra:
            self.asking_poly_extra = True
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
            "Part 2: Wise Man Questions", True, (25, 25, 35))
        surface.blit(title, (self.w // 2 - title.get_width() // 2, 40))

        fields_text = ", ".join([str(x) for x in self.inferred_fields[:3]])
        meta = self.font_small.render(
            f"Fields: {fields_text}", True, (90, 90, 110))
        surface.blit(meta, (60, 95))

        if not self.questions and not self.poly_extra:
            msg = self.font.render(
                "No Part 2 questions found in state.part2_payload.", True, (60, 60, 80))
            surface.blit(msg, (60, 160))
            self.btn_back.draw(surface)
            return

        # Decide what is current prompt
        if self.asking_poly_extra and self.poly_extra:
            q = self.poly_extra
            total = len(self.questions) + 1
            current = len(self.questions) + 1
        else:
            q = self.questions[self.idx]
            total = len(self.questions) + (1 if self.poly_extra else 0)
            current = self.idx + 1

        prompt = str(q.get("prompt", ""))
        qtype = str(q.get("type", "text"))
        qid = str(q.get("id", f"q{current}"))

        step = self.font_small.render(
            f"{current}/{total}   id={qid}   type={qtype}", True, (90, 90, 110))
        surface.blit(step, (60, 125))

        y = 165
        for line in self._wrap(prompt, 60):
            surface.blit(self.font.render(line, True, (40, 40, 55)), (60, y))
            y += 30

        self.btn_back.draw(surface)
        self.btn_next.draw(surface)

        self.modal.draw(surface)

    def _commit_and_next(self) -> None:
        # Normal part2 questions
        if not self.asking_poly_extra:
            q = self.questions[self.idx]
            if not self.modal.done:
                return
            self.answers.append({
                "id": q.get("id", f"q{self.idx+1}"),
                "type": q.get("type", "text"),
                "prompt": q.get("prompt", ""),
                "answer": self.modal.answer,
            })
            self.modal.active = False

            if self.idx < len(self.questions) - 1:
                self.idx += 1
                self._open_current()
                return

            # Done 12 questions, go to poly extra if present
            if self.poly_extra:
                self.asking_poly_extra = True
                self._open_current()
                return

            self._finish()
            return

        # Poly extra question
        if not self.modal.done:
            return
        q = self.poly_extra or {}
        raw = self.modal.answer
        self.answers.append({
            "id": q.get("id", "poly_path"),
            "type": q.get("type", "mcq"),
            "prompt": q.get("prompt", ""),
            "answer": raw,
        })
        self.modal.active = False

        # Best-effort parse
        val = str(raw).lower()
        if "work" in val:
            self.poly_path_choice = "Work"
        elif "uni" in val:
            self.poly_path_choice = "Go to uni"

        self._finish()

    def _open_current(self) -> None:
        if self.asking_poly_extra:
            q = self.poly_extra
        else:
            q = self.questions[self.idx] if self.questions else None

        if isinstance(q, dict) and q.get("type") in ("mcq", "slider", "rating", "text"):
            self.modal.open(q)

    def _finish(self) -> None:
        next_screen = None
        try:
            next_screen = self.back_screen.on_part2_completed(
                inferred_fields=self.inferred_fields,
                part2_answers=self.answers,
                poly_path_choice=self.poly_path_choice,
            )
        except Exception:
            next_screen = None
        self.sm.set(next_screen or self.back_screen)

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
