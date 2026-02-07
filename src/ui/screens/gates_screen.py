from __future__ import annotations
import pygame
import math
from ui.screen_manager import ScreenManager
from app.state import AppState
from core.content_engine import ContentEngine


class GatesScreen:
    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int, engine: ContentEngine):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height
        self.engine = engine

        self.font = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 22)

        self.player = pygame.Rect(80, 360, 32, 32)
        self.gates: list[pygame.Rect] = [
            pygame.Rect(260, 260, 90, 120),
            pygame.Rect(420, 260, 90, 120),
            pygame.Rect(580, 260, 90, 120),
        ]
        self.banner = "Touch a gate to enter."
        self.banner_timer = 2.0

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        speed = 240 * dt
        self.player.x += int((keys[pygame.K_RIGHT] -
                             keys[pygame.K_LEFT]) * speed)
        self.player.y += int((keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed)
        self.player.x = max(0, min(self.w - self.player.width, self.player.x))
        self.player.y = max(0, min(self.h - self.player.height, self.player.y))

        for i, g in enumerate(self.gates):
            if self.player.colliderect(g):
                option = self.state.data.suggested_options[i]
                self.state.data.chosen_gate = option
                from ui.screens.gate_scene_screen import GateSceneScreen
                self.sm.set(GateSceneScreen(self.sm, self.state,
                            self.w, self.h, self.engine, option))
                return

        if self.banner_timer > 0:
            self.banner_timer -= dt
            if self.banner_timer <= 0:
                self.banner = ""

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((230, 238, 245))

        surface.blit(self.font.render(
            "Three Gates", True, (30, 30, 40)), (30, 30))
        surface.blit(self.font_small.render(
            "Top-down view. Use arrow keys.", True, (80, 80, 95)), (30, 62))

        labels = self.state.data.suggested_options or [
            "Gate A", "Gate B", "Gate C"]
        for i, g in enumerate(self.gates):
            pygame.draw.rect(surface, (150, 150, 160), g, border_radius=10)
            pygame.draw.rect(surface, (90, 90, 100), g, 2, border_radius=10)
            txt = self.font_small.render(labels[i], True, (20, 20, 30))
            surface.blit(txt, (g.centerx - txt.get_width()//2, g.y - 24))

        pygame.draw.rect(surface, (40, 90, 200), self.player, border_radius=8)

        if self.banner:
            b = pygame.Rect(30, self.h - 70, self.w - 60, 42)
            pygame.draw.rect(surface, (255, 255, 255), b, border_radius=10)
            pygame.draw.rect(surface, (190, 190, 200), b, 2, border_radius=10)
            surface.blit(self.font.render(self.banner, True,
                         (30, 30, 40)), (b.x + 12, b.y + 10))
