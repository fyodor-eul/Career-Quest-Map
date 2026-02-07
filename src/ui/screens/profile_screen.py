# FILE: src/ui/screens/profile_screen.py

from __future__ import annotations
import pygame

from ui.widgets import Button, TextInput, ChoiceGroup
from ui.screen_manager import ScreenManager
from app.state import AppState


class ProfileScreen:
    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height

        self.font_title = pygame.font.Font(None, 44)
        self.font = pygame.font.Font(None, 26)
        self.font_hint = pygame.font.Font(None, 22)

        self.name_input = TextInput(
            pygame.Rect(260, 150, 380, 44),
            pygame.font.Font(None, 28),
            "Your name",
        )

        self.edu_group = ChoiceGroup(
            260,
            240,
            ["Secondary School", "JC", "Poly"],
            pygame.font.Font(None, 26),
        )

        self.confirm = Button(
            pygame.Rect(width // 2 - 90, height - 120, 180, 50),
            "Confirm",
            pygame.font.Font(None, 32),
        )

        self.ask_poly_course = False
        self.poly_input = TextInput(
            pygame.Rect(260, 360, 380, 44),
            pygame.font.Font(None, 28),
            "Current poly course",
        )

        self.error_msg: str | None = None
        self.error_until = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        self.name_input.handle_event(event)
        self.edu_group.handle_event(event)

        if self.ask_poly_course:
            self.poly_input.handle_event(event)

        if event.type == pygame.MOUSEMOTION:
            self.confirm.handle_mouse(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.confirm.clicked(event.pos):
                self._on_confirm()

    def _on_confirm(self) -> None:
        name = self.name_input.text.strip()
        edu = ["Secondary School", "JC", "Poly"][self.edu_group.selected]

        if not name:
            self._set_error("Enter your name.")
            return

        self.state.profile.user_name = name
        self.state.profile.education_status = edu  # type: ignore

        if edu == "Poly":
            self.ask_poly_course = True
            course = self.poly_input.text.strip()

            # First confirm on Poly should just reveal the course box, not force proceed.
            if not course:
                self._set_error("Enter your current poly course.")
                return

            self.state.profile.poly_course_of_study = course
            self._go_training()
            return

        # Non-poly
        self.ask_poly_course = False
        self.poly_input.text = ""
        self.state.profile.poly_course_of_study = None
        self._go_training()

    def _set_error(self, msg: str, seconds: float = 2.2) -> None:
        self.error_msg = msg
        self.error_until = pygame.time.get_ticks() / 1000.0 + seconds

    def _go_training(self) -> None:
        self.state.world.stage = "training"
        from ui.screens.training_map_screen import TrainingMapScreen
        self.sm.set(TrainingMapScreen(self.sm, self.state, self.w, self.h))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((245, 245, 250))

        title = self.font_title.render("Your Profile", True, (25, 25, 35))
        surface.blit(title, (self.w // 2 - title.get_width() // 2, 60))

        surface.blit(self.font.render("Name", True, (40, 40, 50)), (260, 120))
        self.name_input.draw(surface)

        surface.blit(self.font.render("Education status",
                     True, (40, 40, 50)), (260, 210))
        self.edu_group.draw(surface)

        selected_edu = ["Secondary School", "JC",
                        "Poly"][self.edu_group.selected]
        self.ask_poly_course = (selected_edu == "Poly")

        if self.ask_poly_course:
            surface.blit(
                self.font.render(
                    "If Poly, what course are you in?", True, (40, 40, 50)),
                (260, 330),
            )
            self.poly_input.draw(surface)

        if self.error_msg and (pygame.time.get_ticks() / 1000.0) < self.error_until:
            err = self.font_hint.render(self.error_msg, True, (180, 60, 60))
            surface.blit(err, (260, self.h - 170))
        else:
            self.error_msg = None

        self.confirm.draw(surface)
