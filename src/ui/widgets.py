from __future__ import annotations
import pygame


class Button:
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font):
        self.rect = rect
        self.text = text
        self.font = font
        self.hover = False

    def handle_mouse(self, pos: tuple[int, int]) -> None:
        self.hover = self.rect.collidepoint(pos)

    def clicked(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def draw(self, surface: pygame.Surface) -> None:
        bg = (30, 120, 220) if not self.hover else (50, 150, 245)
        pygame.draw.rect(surface, bg, self.rect, border_radius=12)
        label = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(label, (self.rect.centerx - label.get_width() //
                     2, self.rect.centery - label.get_height()//2))


class TextInput:
    def __init__(self, rect: pygame.Rect, font: pygame.font.Font, placeholder: str = ""):
        self.rect = rect
        self.font = font
        self.placeholder = placeholder
        self.active = False
        self.text = ""

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return
            else:
                if len(self.text) < 24 and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=10)
        pygame.draw.rect(surface, (60, 60, 60) if self.active else (
            160, 160, 160), self.rect, 2, border_radius=10)
        shown = self.text if self.text else self.placeholder
        col = (40, 40, 40) if self.text else (150, 150, 150)
        label = self.font.render(shown, True, col)
        surface.blit(label, (self.rect.x + 10, self.rect.y +
                     (self.rect.height - label.get_height())//2))


class ChoiceGroup:
    def __init__(self, x: int, y: int, options: list[str], font: pygame.font.Font):
        self.options = options
        self.font = font
        self.selected = 0
        self.items: list[pygame.Rect] = []
        yy = y
        for _ in options:
            self.items.append(pygame.Rect(x, yy, 18, 18))
            yy += 34

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, r in enumerate(self.items):
                if r.collidepoint(event.pos):
                    self.selected = i

    def draw(self, surface: pygame.Surface) -> None:
        for i, r in enumerate(self.items):
            pygame.draw.rect(surface, (255, 255, 255), r)
            pygame.draw.rect(surface, (80, 80, 80), r, 2)
            if i == self.selected:
                pygame.draw.circle(surface, (30, 120, 220), r.center, 5)
            label = self.font.render(self.options[i], True, (30, 30, 30))
            surface.blit(label, (r.right + 10, r.y - 2))
