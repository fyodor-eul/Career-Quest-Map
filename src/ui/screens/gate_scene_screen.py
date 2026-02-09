# FILE: src/ui/screens/gate_scene_screen.py

from __future__ import annotations

import os
import time
from typing import Optional, Tuple, Any

import pygame

from ui.screen_manager import ScreenManager
from app.state import AppState
from app.config import AppConfig

from core.content_engine import ContentEngine
from integrations.llm_client import LLMClient


class GateSceneScreen:
    """
    Gate scene (non top-down).
    - Shows wise man dialog with course/career info from ContentEngine.gen_gate_scene
    - Asks Yes/No
    - If Yes, shows dragon quests and resources
    - Returns back to training map
    """

    def __init__(
        self,
        sm: ScreenManager,
        state: AppState,
        width: int,
        height: int,
        back_screen,
        option_name: str,
    ):
        self.sm = sm
        self.state = state
        self.w = width
        self.h = height
        self.back_screen = back_screen
        self.option_name = option_name

        self.cfg = AppConfig()
        self.engine = self._build_content_engine()

        self.font_title = pygame.font.Font(None, 40)
        self.font = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 22)

        base_assets = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.assets_dir = os.path.abspath(base_assets)

        self.bg_img = self._safe_load_image(
            "gate_background.png", scale=(self.w, self.h)
        )  # Put gate_background.png here

        self.wise_man_img = self._safe_load_image(
            "wise_man_gate.png", scale=(80, 80)
        )  # Put wise_man_gate.png here
        self.dragon_img = self._safe_load_image(
            "dragon_warrior.png", scale=(90, 90)
        )  # Put dragon_warrior.png here

        self.toast: Optional[str] = None
        self.toast_until = 0.0

        edu = getattr(self.state.profile,
                      "education_status", "Secondary School")
        poly_choice = getattr(self.state.profile, "poly_path_choice", None)
        self.work_path = bool(edu == "Poly" and poly_choice == "Work")

        # IMPORTANT: match ContentEngine.gen_gate_scene(option_name, work_path)
        self.payload = self.engine.gen_gate_scene(
            option_name=self.option_name,
            work_path=self.work_path,
        )

        if not hasattr(self.state, "gate_choices") or not isinstance(getattr(self.state, "gate_choices"), dict):
            setattr(self.state, "gate_choices", {})
        self.state.gate_choices[self.option_name] = {"choice": None}

        self.phase = "info"  # info -> ask -> dragon -> done
        self.lines: list[str] = self._build_info_lines(
            self.payload, self.option_name)
        self.line_idx = 0

        self.dragon_lines: list[str] = []

        self.player_x = 80
        self.player_y = self.h - 140
        self.player_speed = 3

        self.wise_x = self.w - 220
        self.wise_y = self.h - 170

        self.dragon_x = self.w - 160
        self.dragon_y = self.h - 170

        self.right_wall_x = self.w - 120
        self.can_go_right = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._return_to_map()
                return

            if event.key == pygame.K_RETURN:
                self._advance_dialog()
                return

            if self.phase == "ask":
                ch = event.unicode
                if event.key in (pygame.K_y, pygame.K_1) or ch in ("y", "Y", "1"):
                    self._choose_yes()
                    return
                if event.key in (pygame.K_n, pygame.K_2) or ch in ("n", "N", "2"):
                    self._choose_no()
                    return

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()

        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.player_speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.player_speed

        self.player_x += dx

        if self.player_x < 20:
            self.player_x = 20

        if not self.can_go_right and self.player_x > self.right_wall_x - 40:
            self.player_x = self.right_wall_x - 40
        if self.can_go_right and self.player_x > self.w - 60:
            self.player_x = self.w - 60

    def draw(self, surface: pygame.Surface) -> None:
        if self.bg_img:
            surface.blit(self.bg_img, (0, 0))
        else:
            surface.fill((245, 245, 250))

        title = self.font_title.render(self.option_name, True, (25, 25, 35))
        surface.blit(title, (self.w // 2 - title.get_width() // 2, 26))

        if self.wise_man_img:
            surface.blit(self.wise_man_img, (self.wise_x, self.wise_y))
        else:
            pygame.draw.rect(surface, (200, 180, 160), pygame.Rect(
                self.wise_x, self.wise_y, 80, 80), border_radius=10)

        if self.phase in ("dragon", "done"):
            if self.dragon_img:
                surface.blit(self.dragon_img, (self.dragon_x, self.dragon_y))
            else:
                pygame.draw.rect(surface, (180, 80, 80), pygame.Rect(
                    self.dragon_x, self.dragon_y, 90, 90), border_radius=10)

        if not self.can_go_right:
            pygame.draw.rect(surface, (80, 80, 90), pygame.Rect(
                self.right_wall_x, 0, 8, self.h))

        pygame.draw.rect(surface, (0, 132, 255), pygame.Rect(
            self.player_x, self.player_y, 36, 44), border_radius=8)

        self._draw_dialog(surface)

        if self.toast and time.time() < self.toast_until:
            self._draw_toast(surface, self.toast)

    def _advance_dialog(self) -> None:
        if self.phase == "info":
            if self.line_idx < len(self.lines) - 1:
                self.line_idx += 1
                return
            self.phase = "ask"
            self.line_idx = 0
            return

        if self.phase == "dragon":
            if self.line_idx < len(self.dragon_lines) - 1:
                self.line_idx += 1
                return
            self.phase = "done"
            self._toast("Quest added. Press ESC to return.", seconds=2.5)
            return

        if self.phase == "done":
            self._return_to_map()
            return

    def _choose_no(self) -> None:
        self.state.gate_choices[self.option_name]["choice"] = "No"
        self._toast("No worries. Try another gate.", seconds=2.0)

        if hasattr(self.back_screen, "gates_zone_active"):
            self.back_screen.gates_zone_active = True

        self._return_to_map()

    def _choose_yes(self) -> None:
        self.state.gate_choices[self.option_name]["choice"] = "Yes"
        self.can_go_right = True

        dragon = self.payload.get("dragon", {}) if isinstance(
            self.payload, dict) else {}
        micro = str(dragon.get("micro_quest_1_week", ""))
        mini = str(dragon.get("mini_project_1_month", ""))
        res = dragon.get("resources", [])

        res_lines: list[str] = []
        if isinstance(res, list):
            for r in res[:5]:
                if isinstance(r, str) and r.strip():
                    res_lines.append("- " + r.strip())

        self.dragon_lines = ["Dragon Warrior: Nice choice."]
        if micro.strip():
            self.dragon_lines.append("1-week quest:")
            self.dragon_lines.append(micro.strip())
        if mini.strip():
            self.dragon_lines.append("1-month mini project:")
            self.dragon_lines.append(mini.strip())
        if res_lines:
            self.dragon_lines.append("Resources:")
            self.dragon_lines.extend(res_lines)

        if "quests" not in self.state.gate_choices[self.option_name]:
            self.state.gate_choices[self.option_name]["quests"] = {}
        self.state.gate_choices[self.option_name]["quests"]["micro_quest_1_week"] = micro
        self.state.gate_choices[self.option_name]["quests"]["mini_project_1_month"] = mini
        self.state.gate_choices[self.option_name]["quests"]["resources"] = res_lines

        self.phase = "dragon"
        self.line_idx = 0

    def _draw_dialog(self, surface: pygame.Surface) -> None:
        box = pygame.Rect(40, self.h - 170, self.w - 80, 120)
        pygame.draw.rect(surface, (20, 20, 30), box, border_radius=14)
        pygame.draw.rect(surface, (90, 90, 110), box, 2, border_radius=14)

        if self.phase == "info":
            speaker = "Wise Man"
            line = self.lines[self.line_idx] if self.lines else ""
            hint = "Enter to continue"
        elif self.phase == "ask":
            speaker = "Wise Man"
            line = "Are you interested?  1) Yes (Y)   2) No (N)"
            hint = "Press Y or N"
        elif self.phase == "dragon":
            speaker = "Dragon Warrior"
            line = self.dragon_lines[self.line_idx] if self.dragon_lines else ""
            hint = "Enter to continue"
        else:
            speaker = "System"
            line = "Return to the gates. Press Enter or ESC."
            hint = "Enter or ESC"

        head = self.font_small.render(speaker, True, (255, 255, 255))
        surface.blit(head, (box.x + 14, box.y + 10))

        wrapped = self._wrap(line, 62)
        y = box.y + 36
        for w in wrapped[:3]:
            txt = self.font.render(w, True, (235, 235, 245))
            surface.blit(txt, (box.x + 14, y))
            y += 28

        hint_s = self.font_small.render(hint, True, (180, 180, 200))
        surface.blit(
            hint_s, (box.right - hint_s.get_width() - 14, box.bottom - 26))

    def _build_info_lines(self, payload: dict[str, Any], option_name: str) -> list[str]:
        info = payload.get("info_dialog_lines", [])
        lines: list[str] = [f"Wise Man: This gate is {option_name}."]

        if isinstance(info, list):
            for s in info:
                if isinstance(s, str) and s.strip():
                    lines.append(s.strip())

        if self.work_path:
            ws = payload.get("work_style_line", "")
            sal = payload.get("salary_outlook_line", "")
            if isinstance(ws, str) and ws.strip():
                lines.append(ws.strip())
            if isinstance(sal, str) and sal.strip():
                lines.append(sal.strip())

        if not lines:
            lines = ["Wise Man: Let me share what this path looks like."]
        return lines

    def _build_content_engine(self) -> ContentEngine:
        llm = LLMClient(
            self.cfg.azure_endpoint,
            self.cfg.azure_api_key,
            self.cfg.azure_api_version,
            self.cfg.azure_deployment,
        )
        return ContentEngine(llm)

    def _toast(self, text: str, seconds: float = 2.0) -> None:
        self.toast = text
        self.toast_until = time.time() + seconds

    def _draw_toast(self, surface: pygame.Surface, text: str) -> None:
        padding = 10
        surf = self.font_small.render(text, True, (255, 255, 255))
        w = surf.get_width() + padding * 2
        h = surf.get_height() + padding * 2
        x = (self.w - w) // 2
        y = 16
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (20, 20, 30), rect, border_radius=10)
        surface.blit(surf, (x + padding, y + padding))

    def _wrap(self, text: str, max_chars: int) -> list[str]:
        words = str(text).split()
        lines: list[str] = []
        line: list[str] = []
        count = 0
        for w in words:
            add = len(w) + (1 if line else 0)
            if count + add <= max_chars:
                line.append(w)
                count += add
            else:
                lines.append(" ".join(line))
                line = [w]
                count = len(w)
        if line:
            lines.append(" ".join(line))
        return lines

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

    def _return_to_map(self) -> None:
        if hasattr(self.back_screen, "gates_zone_active"):
            self.back_screen.gates_zone_active = True
        if hasattr(self.back_screen, "on_gate_exit"):
            try:
                self.back_screen.on_gate_exit()
            except Exception:
                pass
        self.sm.set(self.back_screen)
