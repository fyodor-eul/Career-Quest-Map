# FILE: src/ui/screen_manager.py

from __future__ import annotations
import pygame
from ui.screen_base import Screen


class ScreenManager:
    """
    Minimal screen router.

    Your app loop should call:
    - sm.handle_event(event)
    - sm.update(dt)
    - sm.draw(surface)
    """

    def __init__(self, start_screen: Screen):
        self.current: Screen = start_screen

    def set(self, screen: Screen) -> None:
        self.current = screen

    def handle_event(self, event: pygame.event.Event) -> None:
        self.current.handle_event(event)

    def update(self, dt: float) -> None:
        self.current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.current.draw(surface)
