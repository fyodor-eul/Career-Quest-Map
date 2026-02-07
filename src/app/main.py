from __future__ import annotations
import os
import pygame

from app.config import AppConfig
from app.state import AppState
from ui.screen_manager import ScreenManager
from ui.screens.start_screen import StartScreen


def main() -> None:
    cfg = AppConfig()
    pygame.init()
    pygame.display.set_caption("Career Quest Map")
    screen = pygame.display.set_mode((cfg.width, cfg.height))
    clock = pygame.time.Clock()

    state = AppState()
    sm = ScreenManager(StartScreen(
        None, state, cfg.width, cfg.height))  # type: ignore
    # Fix circular init
    sm.set(StartScreen(sm, state, cfg.width, cfg.height))

    running = True
    while running:
        dt = clock.tick(cfg.fps) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            sm.handle_event(event)
        sm.update(dt)
        sm.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
