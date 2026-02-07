from __future__ import annotations
import os
import pygame


class Assets:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.images: dict[str, pygame.Surface] = {}

    def _img_path(self, rel: str) -> str:
        return os.path.join(self.base_dir, rel)

    def load_image(self, key: str, rel_path: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        path = self._img_path(rel_path)
        # Placeholder safety: create a colored box if missing
        if not os.path.exists(path):
            surf = pygame.Surface(size or (48, 48))
            surf.fill((200, 200, 210))
            self.images[key] = surf
            return surf

        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        self.images[key] = img
        return img

    def get(self, key: str) -> pygame.Surface:
        return self.images[key]
