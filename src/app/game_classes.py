import pygame

#===============Constants===================
GAME_WIDTH = 900
GAME_HEIGHT = 600

OUTSIDE_SPAWN = (50, 300)
HOME_SPAWN    = (100, 300)

# Colors 
WHITE = (255,255,255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0,0,0)

# Game State
CHAPTER1 = "chapter1"
## Profile
PROFILE = "profile"
## Chapter I
OUTSIDE = "outside"
HOME = "home"
WISEMAN = "wiseman"
GATE = "gate"
## Chapter II
CHAPTER2 = "chapter2"
PORTAL1 = "portal1"
PORTAL2 = "portal2"
PORTAL3 = "portal3"

#================ Player =========================
class Player:
    def __init__(self, x, y, width, height, img_path, speed):

        # Load player images for all directions
        self.img_up    = pygame.transform.scale(pygame.image.load(img_path + "north.png").convert_alpha(),     (width, height))
        self.img_down  = pygame.transform.scale(pygame.image.load(img_path + "south.png").convert_alpha(),     (width, height))
        self.img_left  = pygame.transform.scale(pygame.image.load(img_path + "west.png").convert_alpha(),      (width, height))
        self.img_right = pygame.transform.scale(pygame.image.load(img_path + "east.png").convert_alpha(),      (width, height))

        # Player Attributes
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = speed # pixel/second
        self.img_path = img_path 
        self.img = self.img_down

    def move(self, dt, game_width, game_height):
        keys = pygame.key.get_pressed()

        # Move Up
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_k]) and self.rect.y >= 0:
            self.rect.y -= self.speed * dt
            self.img = self.img_up

        # Move Down
        if (keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_j]) and self.rect.y <= game_height - self.rect.height:
            self.rect.y += self.speed * dt
            self.img = self.img_down

        # Move Left
        if (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_h]) and self.rect.x >= 0:
            self.rect.x -= self.speed * dt
            self.img = self.img_left

        # Move Right
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_l]) and self.rect.x <= game_width - self.rect.width:
            self.rect.x += self.speed * dt
            self.img = self.img_right

    def draw(self, surface):
        surface.blit(self.img, self.rect)

class Structure:
    def __init__(self, x, y, width, height, img_path, bg_img_path):
        img = pygame.image.load(img_path).convert_alpha()
        img = pygame.transform.scale(img, (width, height))

        bg_img = pygame.image.load(bg_img_path)
        bg_img = pygame.transform.scale(bg_img, (GAME_WIDTH, GAME_HEIGHT))

        self.img = img
        self.bg = bg_img
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface):
        surface.blit(self.img, self.rect)
