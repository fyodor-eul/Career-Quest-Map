from __future__ import annotations
import pygame
from ui.screen_manager import ScreenManager
from app.state import AppState
from core.content_engine import ContentEngine


class WiseManScreen:
    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int, engine: ContentEngine, back_screen):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height
        self.engine = engine
        self.back_screen = back_screen

        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)

        self.step = 0
        self.lines: list[str] = []
        self._build_analysis()

    def _build_analysis(self) -> None:
        edu = self.state.profile.education_status
        poly_choice = self.state.profile.poly_path_choice
        inferred_fields = getattr(self.state, "inferred_fields", self.state.data.inferred_fields)
        part2_answers = getattr(self.state, "part2_answers", self.state.data.part2_answers)
        payload = self.engine.gen_analysis(
            edu, poly_choice, inferred_fields, part2_answers)
        self.state.data.strength_tags = payload["strength_tags"]
        self.state.data.work_style_tags = payload["work_style_tags"]
        self.state.data.feedback_lines = payload["feedback_lines"]
        self.state.data.suggested_options = payload["suggested_options"]
        setattr(self.state, "analysis_payload", payload)

        self.lines = []
        self.lines.append("Strength tags: " +
                          ", ".join(self.state.data.strength_tags))
        self.lines.append(
            "Work style: " + ", ".join(self.state.data.work_style_tags))
        self.lines.extend(self.state.data.feedback_lines)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.step += 1
            if self.step >= len(self.lines):
                if hasattr(self.back_screen, "on_analysis_completed"):
                    self.back_screen.on_analysis_completed()
                self.sm.set(self.back_screen)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((245, 245, 250))

        title = self.font.render("Wise Man", True, (30, 30, 40))
        surface.blit(title, (30, 30))

        box = pygame.Rect(30, 110, self.w - 60, 170)
        pygame.draw.rect(surface, (255, 255, 255), box, border_radius=12)
        pygame.draw.rect(surface, (190, 190, 200), box, 2, border_radius=12)

        idx = min(self.step, len(self.lines)-1)
        line = self.lines[idx] if self.lines else ""
        surface.blit(self.font.render(line, True, (30, 30, 40)),
                     (box.x + 16, box.y + 18))

        hint = self.font_small.render("Press Enter", True, (120, 120, 130))
        surface.blit(
            hint, (box.right - hint.get_width() - 16, box.bottom - 28))
