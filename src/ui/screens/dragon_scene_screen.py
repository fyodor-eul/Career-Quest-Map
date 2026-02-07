from __future__ import annotations
import pygame
from ui.screen_manager import ScreenManager
from app.state import AppState
from core.content_engine import ContentEngine
from core.persistence import save_run
from app.config import AppConfig


class DragonSceneScreen:
    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int, engine: ContentEngine, option_name: str, gate_payload: dict):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height
        self.engine = engine
        self.option_name = option_name

        self.font = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 22)

        # Extract dragon quests
        dragon = gate_payload["dragon"]
        self.state.data.dragon_micro_quest = dragon["micro_quest_1_week"]
        self.state.data.dragon_mini_project = dragon["mini_project_1_month"]
        self.state.data.dragon_resources = dragon["resources"]

        self.lines = [
            "Dragon Warrior",
            self.state.data.dragon_micro_quest,
            self.state.data.dragon_mini_project,
            "Resources: " + ", ".join(self.state.data.dragon_resources[:4]),
            "Press Enter to finish."
        ]
        self.i = 0
        self.saved_path: str | None = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.i += 1
            if self.i >= len(self.lines):
                cfg = AppConfig()
                self.saved_path = save_run(self.state, cfg.save_dir)
                from ui.screens.end_screen import EndScreen
                self.sm.set(EndScreen(self.sm, self.state,
                            self.w, self.h, self.saved_path))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((240, 235, 245))
        # Placeholder: "Put gate scene background here"
        pygame.draw.rect(surface, (230, 220, 235),
                         pygame.Rect(0, 0, self.w, self.h), 0)

        box = pygame.Rect(30, 30, self.w - 60, 170)
        pygame.draw.rect(surface, (255, 255, 255), box, border_radius=12)
        pygame.draw.rect(surface, (190, 190, 200), box, 2, border_radius=12)

        idx = min(self.i, len(self.lines)-1)
        line = self.lines[idx]
        surface.blit(self.font.render(
            line[:70], True, (30, 30, 40)), (box.x + 12, box.y + 18))
        surface.blit(self.font_small.render("Press Enter", True,
                     (120, 120, 130)), (box.right - 140, box.bottom - 26))
