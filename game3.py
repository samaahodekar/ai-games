Python 3.14.6 (tags/v3.14.6:c63aec6, Jun 10 2026, 10:26:10) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import math
import random
import sys
import pygame

# Initialize Pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Colors
SKY_BLUE = (25, 30, 45)
GROUND_COLOR = (60, 70, 90)
PLATFORM_COLOR = (80, 95, 120)
WHITE = (240, 240, 250)
YELLOW = (255, 215, 0)
RED = (230, 60, 60)
GREEN = (50, 205, 50)
BLUE = (70, 130, 235)
ORANGE = (255, 140, 0)


class Camera:

  def __init__(self, width, height):
    self.camera = pygame.Rect(0, 0, width, height)
    self.width = width
    self.height = height

  def apply(self, entity):
    if hasattr(entity, "rect"):
      return entity.rect.move(self.camera.topleft)
    elif isinstance(entity, pygame.Rect):
      return entity.move(self.camera.topleft)
    return entity

  def apply_point(self, pos):
    return (pos[0] + self.camera.topleft[0], pos[1] + self.camera.topleft[1])

  def update(self, target):
    x = -target.rect.centerx + SCREEN_WIDTH // 2
    y = -target.rect.centery + SCREEN_HEIGHT // 2
    # Clamp camera to level bounds
    x = min(0, x)  # Don't scroll past left
    x = max(-(self.width - SCREEN_WIDTH), x)  # Don't scroll past right
    y = min(0, y)
    y = max(-(self.height - SCREEN_HEIGHT), y)
    self.camera = pygame.Rect(x, y, self.width, self.height)


class Particle:

  def __init__(self, x, y, color, velocity, lifetime, size=4):
    self.x = x
    self.y = y
    self.color = color
    self.vx, self.vy = velocity
    self.lifetime = lifetime
    self.max_lifetime = lifetime
    self.size = size

  def update(self):
    self.x += self.vx
    self.y += self.vy
    self.lifetime -= 1

  def draw(self, surface, camera):
    if self.lifetime > 0:
      pos = camera.apply_point((int(self.x), int(self.y)))
      pygame.draw.circle(surface, self.color, pos, max(1, int(self.size)))


class Player:

  def __init__(self, x, y):
    self.rect = pygame.Rect(x, y, 32, 48)
    self.x = float(x)
    self.y = float(y)
    self.vx = 0.0
    self.vy = 0.0
    self.speed = 5.0
    self.jump_force = -12.5
    self.gravity = 0.55
    self.is_grounded = False
    self.max_hp = 100
    self.hp = 100
    self.facing_right = True

  def update(self, keys, platforms):
    # Horizontal Movement
    dx = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
      dx = -1
      self.facing_right = False
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
      dx = 1
      self.facing_right = True

    self.vx = dx * self.speed
    self.x += self.vx
    self.rect.x = int(self.x)

    # Horizontal collision check
    for p in platforms:
      if self.rect.colliderect(p):
        if self.vx > 0:
          self.rect.right = p.left
        elif self.vx < 0:
          self.rect.left = p.right
        self.x = self.rect.x

    # Vertical Movement & Gravity
    self.vy += self.gravity
    if self.vy > 12:
      self.vy = 12
    self.y += self.vy
    self.rect.y = int(self.y)

    self.is_grounded = False
    # Vertical collision check
    for p in platforms:
      if self.rect.colliderect(p):
        if self.vy > 0:
          self.rect.bottom = p.top
          self.vy = 0
          self.is_grounded = True
        elif self.vy < 0:
          self.rect.top = p.bottom
          self.vy = 0
        self.y = self.rect.y

  def jump(self):
    if self.is_grounded:
      self.vy = self.jump_force
      self.is_grounded = False
      return True
    return False

  def draw(self, surface, camera):
    draw_rect = camera.apply(self.rect)
    pygame.draw.rect(surface, BLUE, draw_rect, border_radius=6)
    pygame.draw.rect(surface, WHITE, draw_rect, 2, border_radius=6)


class Enemy:

  def __init__(self, x, y, min_x, max_x):
    self.rect = pygame.Rect(x, y, 32, 32)
    self.x = float(x)
    self.y = float(y)
    self.min_x = min_x
    self.max_x = max_x
    self.vx = 2.0
    self.hp = 30

  def update(self):
    self.x += self.vx
    if self.x < self.min_x or self.x > self.max_x:
      self.vx *= -1
      self.x = max(self.min_x, min(self.max_x, self.x))
    self.rect.x = int(self.x)

  def draw(self, surface, camera):
    draw_rect = camera.apply(self.rect)
    pygame.draw.rect(surface, RED, draw_rect, border_radius=4)
    pygame.draw.rect(surface, WHITE, draw_rect, 1, border_radius=4)


class Coin:

  def __init__(self, x, y):
    self.rect = pygame.Rect(x, y, 20, 20)
    self.x = x
    self.y = y
    self.collected = False

  def draw(self, surface, camera):
    if not self.collected:
      center = camera.apply_point((self.x + 10, self.y + 10))
      pygame.draw.circle(surface, YELLOW, center, 10)
      pygame.draw.circle(surface, WHITE, center, 10, 2)


class Game:

  def __init__(self):
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyber Platformer - Python Game")
    self.clock = pygame.time.Clock()
    self.font = pygame.font.SysFont("Arial", 20)
    self.big_font = pygame.font.SysFont("Arial", 40, bold=True)
    self.reset_game()

  def reset_game(self):
    self.level_width = 3000
    self.level_height = 1000
    self.camera = Camera(self.level_width, self.level_height)
    self.player = Player(100, 700)
    self.particles = []
    self.score = 0
    self.level = 1
    self.game_state = "PLAYING"

    # Build Level Platforms, Enemies, and Coins
    self.platforms = [
        # Ground floor
        pygame.Rect(0, 850, 3000, 150),
        # Platforms
        pygame.Rect(300, 720, 250, 25),
        pygame.Rect(650, 600, 200, 25),
        pygame.Rect(950, 500, 300, 25),
        pygame.Rect(1350, 650, 220, 25),
        pygame.Rect(1650, 520, 250, 25),
        pygame.Rect(2000, 420, 250, 25),
        pygame.Rect(2350, 550, 200, 25),
        pygame.Rect(2650, 400, 250, 25),
    ]

    self.enemies = [
        Enemy(400, 680, 300, 520),
        Enemy(1000, 460, 950, 1200),
        Enemy(1700, 480, 1650, 1880),
        Enemy(2050, 380, 2000, 2220),
    ]

    self.coins = [
        Coin(350, 670),
        Coin(720, 550),
        Coin(1050, 450),
        Coin(1420, 600),
        Coin(1750, 470),
        Coin(2100, 370),
        Coin(2400, 500),
        Coin(2750, 350),
    ]

    # Goal Door at the end
    self.goal_rect = pygame.Rect(2800, 300, 50, 100)

  def run(self):
    while True:
      self.handle_events()
      self.update()
      self.draw()
      self.clock.tick(FPS)

  def handle_events(self):
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()
        if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
          if self.player.jump():
            # Spawn jump particles
            for _ in range(6):
              self.particles.append(
                  Particle(
                      self.player.rect.centerx,
                      self.player.rect.bottom,
                      WHITE,
                      (random.uniform(-2, 2), random.uniform(-1, 0)),
                      15,
                      3,
                  )
              )
        if self.game_state in ["GAME_OVER", "VICTORY"] and event.key == pygame.K_r:
          self.reset_game()

  def update(self):
    if self.game_state != "PLAYING":
      return

    keys = pygame.key.get_pressed()
    self.player.update(keys, self.platforms)
    self.camera.update(self.player)

    # Update Enemies
    for enemy in self.enemies:
      enemy.update()
      if self.player.rect.colliderect(enemy.rect):
        # Check if player lands on top of enemy (stomp mechanic)
        if self.player.vy > 0 and self.player.rect.bottom <= enemy.rect.centery + 10:
          self.enemies.remove(enemy)
          self.score += 200
          self.player.vy = -8.0  # Bounce off enemy
          for _ in range(10):
            self.particles.append(
                Particle(
                    enemy.rect.centerx,
                    enemy.rect.centery,
                    GREEN,
                    (random.uniform(-3, 3), random.uniform(-3, 3)),
                    20,
                    4,
                )
            )
          break
        else:
          # Player takes damage
          self.player.hp -= 1
          if self.player.hp <= 0:
            self.game_state = "GAME_OVER"

    # Update Coins
    for coin in self.coins:
      if not coin.collected and self.player.rect.colliderect(coin.rect):
        coin.collected = True
        self.score += 100
        for _ in range(8):
          self.particles.append(
              Particle(
                  coin.x + 10,
                  coin.y + 10,
                  YELLOW,
                  (random.uniform(-2, 2), random.uniform(-2, 2)),
                  20,
                  3,
              )
          )

    # Update Particles
    for p in self.particles[:]:
      p.update()
      if p.lifetime <= 0:
        self.particles.remove(p)

    # Check Goal Reached
    if self.player.rect.colliderect(self.goal_rect):
      self.game_state = "VICTORY"

    # Fall out of bounds check
    if self.player.rect.top > self.level_height:
      self.game_state = "GAME_OVER"

  def draw(self):
    self.screen.fill(SKY_BLUE)

    # Draw Platforms
    for p in self.platforms:
      draw_rect = self.camera.apply(p)
      pygame.draw.rect(self.screen, PLATFORM_COLOR, draw_rect, border_radius=4)
      pygame.draw.rect(self.screen, WHITE, draw_rect, 1, border_radius=4)

    # Draw Goal Door
    goal_draw = self.camera.apply(self.goal_rect)
    pygame.draw.rect(self.screen, GREEN, goal_draw, border_radius=6)
    pygame.draw.rect(self.screen, WHITE, goal_draw, 2, border_radius=6)

    # Draw Coins
    for coin in self.coins:
      coin.draw(self.screen, self.camera)

    # Draw Enemies
    for enemy in self.enemies:
      enemy.draw(self.screen, self.camera)

    # Draw Particles
    for p in self.particles:
      p.draw(self.screen, self.camera)

    # Draw Player
    self.player.draw(self.screen, self.camera)

    # Draw HUD
    self.draw_hud()

    # Game Over / Victory Overlay
    if self.game_state in ["GAME_OVER", "VICTORY"]:
      overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
      overlay.fill((0, 0, 0, 180))
      self.screen.blit(overlay, (0, 0))

      msg = "VICTORY!" if self.game_state == "VICTORY" else "GAME OVER"
      color = GREEN if self.game_state == "VICTORY" else RED
      title_surf = self.big_font.render(msg, True, color)
      self.screen.blit(
          title_surf,
          (
              SCREEN_WIDTH // 2 - title_surf.get_width() // 2,
              SCREEN_HEIGHT // 2 - 50,
          ),
      )

      restart_surf = self.font.render(
          "Press 'R' to Restart or 'ESC' to Quit", True, WHITE
      )
      self.screen.blit(
          restart_surf,
...           (
...               SCREEN_WIDTH // 2 - restart_surf.get_width() // 2,
...               SCREEN_HEIGHT // 2 + 15,
...           ),
...       )
... 
...     pygame.display.flip()
... 
...   def draw_hud(self):
...     # Health bar
...     bar_w, bar_h = 200, 20
...     hp_pct = max(0, self.player.hp / self.player.max_hp)
...     pygame.draw.rect(self.screen, PLATFORM_COLOR, (20, 20, bar_w, bar_h), border_radius=4)
...     pygame.draw.rect(
...         self.screen, RED, (20, 20, int(bar_w * hp_pct), bar_h), border_radius=4
...     )
...     pygame.draw.rect(self.screen, WHITE, (20, 20, bar_w, bar_h), 2, border_radius=4)
... 
...     hp_text = self.font.render(
...         f"HP: {self.player.hp} / {self.player.max_hp}", True, WHITE
...     )
...     self.screen.blit(hp_text, (30, 22))
... 
...     # Score
...     score_text = self.font.render(f"Score: {self.score}", True, YELLOW)
...     self.screen.blit(score_text, (20, 55))
... 
...     controls_text = self.font.render(
...         "A/D or Arrows: Move | Space/W: Jump | Stomp Enemies to Defeat Them",
...         True,
...         WHITE,
...     )
...     self.screen.blit(controls_text, (20, SCREEN_HEIGHT - 35))
... 
... 
... if __name__ == "__main__":
...   game = Game()
