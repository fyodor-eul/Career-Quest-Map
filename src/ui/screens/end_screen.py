from __future__ import annotations
import pygame
from ui.screen_manager import ScreenManager
from app.state import AppState


class EndScreen:
    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int, saved_path: str | None):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height
        self.saved_path = saved_path
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 22)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((245, 245, 250))
        surface.blit(self.font.render(
            "Run Complete", True, (30, 30, 40)), (30, 60))
        if self.saved_path:
            surface.blit(self.font_small.render(
                "Saved to:", True, (80, 80, 95)), (30, 120))
            surface.blit(self.font_small.render(
                self.saved_path, True, (80, 80, 95)), (30, 150))
        surface.blit(self.font_small.render(
            "Press Esc to quit.", True, (120, 120, 130)), (30, 220))
