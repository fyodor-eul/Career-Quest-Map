from __future__ import annotations
import pygame
from typing import Any


class QuestionModal:
    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.font = pygame.font.Font(None, 26)
        self.font_big = pygame.font.Font(None, 30)
        self.active = False

        self.q: dict[str, Any] | None = None
        self.answer: Any = None
        self.done = False

        self.slider_value = 5
        self.rating_value = 3
        self.text_value = ""
        self.mcq_index = 0

    def open(self, q: dict[str, Any]) -> None:
        self.active = True
        self.done = False
        self.q = q
        self.answer = None
        self.slider_value = 5
        self.rating_value = 3
        self.text_value = ""
        self.mcq_index = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.active or not self.q:
            return

        t = self.q["type"]
        if event.type == pygame.KEYDOWN:
            if t == "mcq":
                opts = self.q.get("options", [])
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.mcq_index = max(0, self.mcq_index - 1)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.mcq_index = min(len(opts)-1, self.mcq_index + 1)
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.answer = opts[self.mcq_index] if opts else None
                    self.done = True
            elif t == "slider":
                scale = self.q["scale"]
                mn, mx = int(scale["min"]), int(scale["max"])
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.slider_value = max(mn, self.slider_value - 1)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.slider_value = min(mx, self.slider_value + 1)
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.answer = self.slider_value
                    self.done = True
            elif t == "rating":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.rating_value = max(1, self.rating_value - 1)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.rating_value = min(5, self.rating_value + 1)
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.answer = self.rating_value
                    self.done = True
            elif t == "text":
                if event.key == pygame.K_BACKSPACE:
                    self.text_value = self.text_value[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.text_value.strip():
                        self.answer = self.text_value.strip()
                        self.done = True
                else:
                    if len(self.text_value) < 60 and event.unicode.isprintable():
                        self.text_value += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active or not self.q:
            return

        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(self.w//2 - 320, self.h//2 - 170, 640, 340)
        pygame.draw.rect(surface, (255, 255, 255), panel, border_radius=14)
        pygame.draw.rect(surface, (190, 190, 200), panel, 2, border_radius=14)

        prompt = self.q["prompt"]
        title = self.font_big.render("Question", True, (30, 30, 40))
        surface.blit(title, (panel.x + 20, panel.y + 18))

        self._blit_wrap(surface, prompt, panel.x + 20,
                        panel.y + 60, panel.width - 40)

        t = self.q["type"]
        y = panel.y + 150

        if t == "mcq":
            opts = self.q.get("options", [])
            for i, opt in enumerate(opts):
                prefix = ">" if i == self.mcq_index else " "
                line = self.font.render(f"{prefix} {opt}", True, (30, 30, 40))
                surface.blit(line, (panel.x + 30, y))
                y += 32
            hint = self.font.render(
                "Up/Down, Enter to select", True, (120, 120, 130))
            surface.blit(hint, (panel.x + 20, panel.bottom - 34))

        if t == "slider":
            scale = self.q["scale"]
            mn, mx = int(scale["min"]), int(scale["max"])
            min_label = str(scale["min_label"])
            max_label = str(scale["max_label"])
            bar = pygame.Rect(panel.x + 60, y, panel.width - 120, 10)
            pygame.draw.rect(surface, (210, 210, 220), bar, border_radius=8)
            k = (self.slider_value - mn) / max(1, (mx - mn))
            knob_x = int(bar.x + k * bar.width)
            pygame.draw.circle(surface, (30, 120, 220),
                               (knob_x, bar.y + 5), 10)
            surface.blit(self.font.render(min_label, True,
                         (90, 90, 105)), (bar.x, bar.y + 18))
            surface.blit(self.font.render(max_label, True, (90, 90, 105)),
                         (bar.right - 10 - self.font.size(max_label)[0], bar.y + 18))
            surface.blit(self.font.render(
                f"Value: {self.slider_value}", True, (30, 30, 40)), (panel.x + 20, y - 34))
            hint = self.font.render(
                "Left/Right, Enter to confirm", True, (120, 120, 130))
            surface.blit(hint, (panel.x + 20, panel.bottom - 34))

        if t == "rating":
            surface.blit(self.font.render(
                f"Rating: {self.rating_value}/5", True, (30, 30, 40)), (panel.x + 20, y - 10))
            for i in range(1, 6):
                col = (30, 120, 220) if i <= self.rating_value else (
                    200, 200, 210)
                pygame.draw.circle(
                    surface, col, (panel.x + 60 + i*60, y + 40), 14)
            hint = self.font.render(
                "Left/Right, Enter to confirm", True, (120, 120, 130))
            surface.blit(hint, (panel.x + 20, panel.bottom - 34))

        if t == "text":
            box = pygame.Rect(panel.x + 20, y, panel.width - 40, 46)
            pygame.draw.rect(surface, (245, 245, 248), box, border_radius=10)
            pygame.draw.rect(surface, (180, 180, 190),
                             box, 2, border_radius=10)
            shown = self.text_value if self.text_value else self.q.get(
                "placeholder", "")
            col = (40, 40, 40) if self.text_value else (150, 150, 160)
            surface.blit(self.font.render(shown, True, col),
                         (box.x + 10, box.y + 12))
            hint = self.font.render(
                "Type, Enter to submit", True, (120, 120, 130))
            surface.blit(hint, (panel.x + 20, panel.bottom - 34))

    def _blit_wrap(self, surface: pygame.Surface, text: str, x: int, y: int, w: int) -> None:
        words = text.split(" ")
        line = ""
        yy = y
        for word in words:
            test = (line + " " + word).strip()
            if self.font.size(test)[0] <= w:
                line = test
            else:
                surface.blit(self.font.render(
                    line, True, (30, 30, 40)), (x, yy))
                yy += 26
                line = word
        if line:
            surface.blit(self.font.render(line, True, (30, 30, 40)), (x, yy))
