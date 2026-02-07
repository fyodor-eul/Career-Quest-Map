from __future__ import annotations
import pygame
from ui.widgets import Button
from ui.screen_manager import ScreenManager
from app.state import AppState


class StartScreen:
    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height
        self.font_title = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 28)
        self.btn = Button(pygame.Rect(width//2 - 90, height //
                          2 + 80, 180, 50), "Start", pygame.font.Font(None, 32))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.btn.handle_mouse(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn.clicked(event.pos):
                self.state.world.stage = "profile"
                from ui.screens.profile_screen import ProfileScreen
                self.sm.set(ProfileScreen(self.sm, self.state, self.w, self.h))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((245, 245, 250))
        title = self.font_title.render("Career Quest Map", True, (25, 25, 35))
        surface.blit(title, (self.w//2 - title.get_width()//2, 130))
        subtitle = self.font.render(
            "Explore your path. Unlock your next quest.", True, (80, 80, 95))
        surface.blit(subtitle, (self.w//2 - subtitle.get_width()//2, 210))
        self.btn.draw(surface)
