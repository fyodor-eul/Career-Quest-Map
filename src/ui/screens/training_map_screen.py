# FILE: src/ui/screens/training_map_screen.py

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Any

import pygame

from app.state import AppState
from ui.screen_manager import ScreenManager

from app.config import AppConfig
from core.content_engine import ContentEngine
from integrations.llm_client import LLMClient


@dataclass
class RectObject:
    rect: pygame.Rect
    label: str


class TrainingMapScreen:
    """
    Top-down training grounds exploration screen.

    Flow implemented:
    - House trigger -> Part 1
    - Wise man proximity -> Part 2
    - After Part 2 -> spawn 3 gates based on suggested_options
    - Touch gate -> route to gate scene screen
    """

    def __init__(self, sm: ScreenManager, state: AppState, width: int, height: int):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height

        self.cfg = AppConfig()
        self.engine = self._build_content_engine()

        self.screen_rect = pygame.Rect(0, 0, self.w, self.h)

        self.bg_color = (245, 245, 250)
        self.ui_text_color = (40, 40, 55)
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)

        base_assets = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.assets_dir = os.path.abspath(base_assets)

        self.bg_img = self._safe_load_image("background.png", scale=(
            self.w, self.h))  # Put background.png here

        self.warrior_up = self._safe_load_image(
            "warrior_up.png", scale=(40, 40))      # Add warrior-up here
        self.warrior_down = self._safe_load_image(
            "warrior_down.png", scale=(40, 40))  # Add warrior-down here
        self.warrior_left = self._safe_load_image(
            "warrior_left.png", scale=(40, 40))  # Add warrior-left here
        self.warrior_right = self._safe_load_image(
            "warrior_right.png", scale=(40, 40))  # Add warrior-right here

        self.wise_man_img = self._safe_load_image(
            "wise_man.png", scale=(48, 48))      # Add wise_man here
        self.house_img = self._safe_load_image(
            "house.png", scale=(96, 96))            # Add house here
        self.gate_img = self._safe_load_image("gate.png", scale=(
            72, 88))              # Add gate.png here (optional)

        self.player_speed = 3
        self.player_rect = pygame.Rect(60, 260, 40, 40)
        self.player_dir = "down"

        self.house = RectObject(pygame.Rect(220, 180, 96, 96), "house")
        self.wise_man = RectObject(pygame.Rect(320, 420, 48, 48), "wise_man")

        self.part1_started = False
        self.part1_done = False
        self.part2_started = False
        self.part2_done = False

        self.show_hint_meet_wise_man = False
        self.show_hint_go_gates = False

        self.toast_text: Optional[str] = None
        self.toast_until = 0.0

        self.wise_man_trigger_dist = 70

        # Gates
        self.gates_spawned = False
        self.gates: list[RectObject] = []
        self.gate_names: list[str] = []
        self.gates_zone_active = False

    # ---------------- core loop ----------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.player_speed
            self.player_dir = "left"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.player_speed
            self.player_dir = "right"

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.player_speed
            self.player_dir = "up"
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.player_speed
            self.player_dir = "down"

        if dx or dy:
            self._move_player(dx, dy)

        # Trigger house entry -> Part 1
        if (not self.part1_started) and self.player_rect.colliderect(self.house.rect):
            self._enter_house_start_part1()

        # Wise man trigger -> Part 2
        if self.part1_done and (not self.part2_started):
            if not self.show_hint_meet_wise_man:
                self.show_hint_meet_wise_man = True
                self._toast("Meet the wise man.", seconds=2.5)

            if self._near(self.player_rect.center, self.wise_man.rect.center, self.wise_man_trigger_dist):
                self._start_part2()

        # After Part 2 -> spawn gates
        if self.part2_done and (not self.gates_spawned):
            self._spawn_gates_from_analysis()

        # If gates exist, touching gate opens gate scene
        if self.gates_zone_active:
            for gate in self.gates:
                if self.player_rect.colliderect(gate.rect):
                    self._enter_gate(gate.label)
                    break

    def draw(self, surface: pygame.Surface) -> None:
        if self.bg_img:
            surface.blit(self.bg_img, (0, 0))
        else:
            surface.fill(self.bg_color)

        self._draw_object(surface, self.house, self.house_img,
                          fallback_color=(200, 200, 230))
        self._draw_object(surface, self.wise_man,
                          self.wise_man_img, fallback_color=(230, 200, 200))

        # Gates
        if self.gates_spawned:
            for gate in self.gates:
                self._draw_gate(surface, gate)

            if not self.show_hint_go_gates:
                self.show_hint_go_gates = True
                self._toast("Choose a gate.", seconds=2.5)

        # Player
        player_img = self._get_player_img()
        if player_img:
            surface.blit(player_img, self.player_rect.topleft)
        else:
            pygame.draw.rect(surface, (0, 120, 255),
                             self.player_rect, border_radius=8)

        if self.toast_text and time.time() < self.toast_until:
            self._draw_toast(surface, self.toast_text)
        elif self.toast_text and time.time() >= self.toast_until:
            self.toast_text = None

    # ---------------- flow triggers ----------------

    def _enter_house_start_part1(self) -> None:
        self.part1_started = True
        self._toast("Entering the house...", seconds=1.0)

        edu = getattr(self.state.profile,
                      "education_status", "Secondary School")
        poly_course = getattr(self.state.profile, "poly_course_of_study", None)

        payload = self.engine.gen_part1(edu, poly_course)
        setattr(self.state, "part1_payload", payload)

        from ui.screens.house_questions_screen import HouseQuestionsScreen
        self.sm.set(HouseQuestionsScreen(
            self.sm, self.state, self.w, self.h, back_screen=self))

    def on_part1_completed(self, part1_answers: list[dict[str, Any]]) -> None:
        setattr(self.state, "part1_answers", part1_answers)
        self.part1_done = True

        # Move outside house
        self.player_rect.topleft = (
            self.house.rect.left - 50, self.house.rect.bottom + 10)
        self._toast("Good. Now meet the wise man.", seconds=2.5)

    def _start_part2(self) -> None:
        self.part2_started = True

        edu = getattr(self.state.profile,
                      "education_status", "Secondary School")
        part1_answers = getattr(self.state, "part1_answers", [])

        payload = self.engine.gen_part2(edu, part1_answers)
        setattr(self.state, "part2_payload", payload)

        from ui.screens.wise_man_questions_screen import WiseManQuestionsScreen
        self.sm.set(WiseManQuestionsScreen(
            self.sm, self.state, self.w, self.h, back_screen=self))

    def on_part2_completed(self, inferred_fields: list[str], part2_answers: list[dict[str, Any]], poly_path_choice: Optional[str] = None) -> None:
        setattr(self.state, "inferred_fields", inferred_fields)
        setattr(self.state, "part2_answers", part2_answers)

        if poly_path_choice:
            self.state.profile.poly_path_choice = poly_path_choice  # type: ignore

        self.part2_done = True

        # Generate analysis now so we can spawn gates
        edu = getattr(self.state.profile,
                      "education_status", "Secondary School")
        poly_choice = getattr(self.state.profile, "poly_path_choice", None)
        analysis = self.engine.gen_analysis(
            edu, poly_choice, inferred_fields, part2_answers)
        setattr(self.state, "analysis_payload", analysis)

        self._toast("Head to the gates.", seconds=2.5)

    # ---------------- gates ----------------

    def _spawn_gates_from_analysis(self) -> None:
        analysis = getattr(self.state, "analysis_payload", None)
        if not isinstance(analysis, dict):
            self._toast("No analysis payload found.", seconds=2.5)
            return

        opts = analysis.get("suggested_options", [])
        if not isinstance(opts, list) or len(opts) != 3:
            self._toast("Need 3 suggested options for gates.", seconds=2.5)
            return

        self.gate_names = [str(x) for x in opts]

        # Place gates on right side area
        gx = self.w - 110
        top = 140
        gap = 140

        self.gates = [
            RectObject(pygame.Rect(gx, top + 0 * gap, 72, 88),
                       self.gate_names[0]),
            RectObject(pygame.Rect(gx, top + 1 * gap, 72, 88),
                       self.gate_names[1]),
            RectObject(pygame.Rect(gx, top + 2 * gap, 72, 88),
                       self.gate_names[2]),
        ]

        self.gates_spawned = True
        self.gates_zone_active = True

        # Optional: teleport player closer so they can see gates fast
        self.player_rect.center = (self.w // 2, self.h // 2)

    def _enter_gate(self, option_name: str) -> None:
        # Disable repeat triggers
        self.gates_zone_active = False

        # Store which gate is being explored
        setattr(self.state, "current_gate_option", option_name)

        from ui.screens.gate_scene_screen import GateSceneScreen
        self.sm.set(GateSceneScreen(self.sm, self.state, self.w,
                    self.h, back_screen=self, option_name=option_name))

    # ---------------- helpers ----------------

    def _build_content_engine(self) -> ContentEngine:
        llm = LLMClient(
            self.cfg.azure_endpoint,
            self.cfg.azure_api_key,
            self.cfg.azure_api_version,
            self.cfg.azure_deployment,
        )
        return ContentEngine(llm)

    def _move_player(self, dx: int, dy: int) -> None:
        self.player_rect.x += dx
        self.player_rect.y += dy
        self.player_rect = self._clamp_to_bounds(self.player_rect)

    def _clamp_to_bounds(self, r: pygame.Rect) -> pygame.Rect:
        if r.left < self.screen_rect.left:
            r.left = self.screen_rect.left
        if r.right > self.screen_rect.right:
            r.right = self.screen_rect.right
        if r.top < self.screen_rect.top:
            r.top = self.screen_rect.top
        if r.bottom > self.screen_rect.bottom:
            r.bottom = self.screen_rect.bottom
        return r

    def _near(self, p1: Tuple[int, int], p2: Tuple[int, int], dist: float) -> bool:
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return (dx * dx + dy * dy) ** 0.5 <= dist

    def _toast(self, text: str, seconds: float = 2.0) -> None:
        self.toast_text = text
        self.toast_until = time.time() + seconds

    def _draw_toast(self, surface: pygame.Surface, text: str) -> None:
        padding = 10
        surf = self.font.render(text, True, (255, 255, 255))
        w, h = surf.get_width() + padding * 2, surf.get_height() + padding * 2
        x = (self.w - w) // 2
        y = self.h - h - 14
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (20, 20, 30), rect, border_radius=10)
        surface.blit(surf, (x + padding, y + padding))

    def _draw_text(self, surface: pygame.Surface, text: str, pos: Tuple[int, int]) -> None:
        surf = self.font.render(text, True, self.ui_text_color)
        surface.blit(surf, pos)

    def _draw_object(self, surface: pygame.Surface, obj: RectObject, img: Optional[pygame.Surface], fallback_color=(200, 200, 200)) -> None:
        if img:
            surface.blit(img, obj.rect.topleft)
        else:
            pygame.draw.rect(surface, fallback_color,
                             obj.rect, border_radius=10)
            self._draw_text(surface, obj.label,
                            (obj.rect.x + 6, obj.rect.y + 6))

    def _draw_gate(self, surface: pygame.Surface, gate: RectObject) -> None:
        if self.gate_img:
            surface.blit(self.gate_img, gate.rect.topleft)
        else:
            pygame.draw.rect(surface, (220, 210, 170),
                             gate.rect, border_radius=10)
            pygame.draw.rect(surface, (120, 110, 80),
                             gate.rect, 2, border_radius=10)

        # Label above gate
        label = gate.label
        text = self.font_small.render(label, True, (20, 20, 30))
        surface.blit(text, (gate.rect.centerx -
                     text.get_width() // 2, gate.rect.y - 22))

    def _get_player_img(self) -> Optional[pygame.Surface]:
        if self.player_dir == "up":
            return self.warrior_up
        if self.player_dir == "down":
            return self.warrior_down
        if self.player_dir == "left":
            return self.warrior_left
        if self.player_dir == "right":
            return self.warrior_right
        return self.warrior_down

    def _safe_load_image(self, filename: str, scale: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
        try:
            path = os.path.join(self.assets_dir, filename)
            if not os.path.exists(path):
                return None
            img = pygame.image.load(path).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            return img
        except Exception:
            return None
