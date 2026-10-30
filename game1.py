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
BLACK = (15, 15, 20)
WHITE = (240, 240, 240)
DARK_GRAY = (40, 40, 50)
LIGHT_GRAY = (100, 100, 110)
RED = (220, 50, 50)
GREEN = (50, 200, 90)
BLUE = (50, 120, 220)
YELLOW = (240, 200, 50)
PURPLE = (150, 50, 200)
ORANGE = (230, 130, 40)


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
    x = -target.x + SCREEN_WIDTH // 2
    y = -target.y + SCREEN_HEIGHT // 2
    # Limit camera to map boundaries
    self.camera = pygame.Rect(x, y, self.width, self.height)


class Particle:

  def __init__(self, x, y, color, velocity, lifetime, size=3):
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
      alpha = int(255 * (self.lifetime / self.max_lifetime))
      pos = camera.apply_point((int(self.x), int(self.y)))
      pygame.draw.circle(surface, self.color, pos, max(1, int(self.size)))


class Bullet:

  def __init__(self, x, y, dx, dy, speed, damage, is_player=True):
    self.x = x
    self.y = y
    self.dx = dx
    self.dy = dy
    self.speed = speed
    self.damage = damage
    self.is_player = is_player
    self.radius = 5 if is_player else 6
    self.rect = pygame.Rect(
        int(x - self.radius), int(y - self.radius), self.radius * 2, self.radius * 2
    )

  def update(self, walls):
    self.x += self.dx * self.speed
    self.y += self.dy * self.speed
    self.rect.topleft = (int(self.x - self.radius), int(self.y - self.radius))

    # Check wall collision
    for wall in walls:
      if self.rect.colliderect(wall):
        return True
    return False

  def draw(self, surface, camera):
    color = YELLOW if self.is_player else PURPLE
    pos = camera.apply_point((int(self.x), int(self.y)))
    pygame.draw.circle(surface, color, pos, self.radius)


class Player:

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.radius = 16
    self.rect = pygame.Rect(
        int(x - self.radius), int(y - self.radius), self.radius * 2, self.radius * 2
    )
    self.speed = 3.5
    self.max_hp = 100
    self.hp = 100
    self.score = 0
    self.gold = 0
    self.shoot_cooldown = 0
    self.weapon_speed = 12
    self.damage = 25

  def update(self, keys, walls):
    dx, dy = 0, 0
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
      dx = -1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
      dx = 1
    if keys[pygame.K_w] or keys[pygame.K_UP]:
      dy = -1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
      dy = 1

    if dx != 0 and dy != 0:
      dx *= 0.7071
      dy *= 0.7071

    # Move X
    self.x += dx * self.speed
    self.rect.x = int(self.x - self.radius)
    for wall in walls:
      if self.rect.colliderect(wall):
        if dx > 0:
          self.rect.right = wall.left
        elif dx < 0:
          self.rect.left = wall.right
        self.x = self.rect.centerx

    # Move Y
    self.y += dy * self.speed
    self.rect.y = int(self.y - self.radius)
    for wall in walls:
      if self.rect.colliderect(wall):
        if dy > 0:
          self.rect.bottom = wall.top
        elif dy < 0:
          self.rect.top = wall.bottom
        self.y = self.rect.centery

    if self.shoot_cooldown > 0:
      self.shoot_cooldown -= 1

  def draw(self, surface, camera):
    pos = camera.apply_point((int(self.x), int(self.y)))
    pygame.draw.circle(surface, BLUE, pos, self.radius)
    pygame.draw.circle(surface, WHITE, pos, self.radius, 2)


class Enemy:

  def __init__(self, x, y, enemy_type="goblin"):
    self.x = x
    self.y = y
    self.type = enemy_type
    if enemy_type == "goblin":
      self.radius = 14
      self.speed = 2.2
      self.hp = 40
      self.max_hp = 40
      self.damage = 10
      self.color = GREEN
      self.attack_range = 25
    elif enemy_type == "orc":
      self.radius = 20
      self.speed = 1.3
      self.hp = 90
      self.max_hp = 90
      self.damage = 25
      self.color = (30, 130, 60)
      self.attack_range = 35
    elif enemy_type == "mage":
      self.radius = 15
      self.speed = 1.5
      self.hp = 50
      self.max_hp = 50
      self.damage = 15
      self.color = PURPLE
      self.attack_range = 250
      self.shoot_cooldown = 0

    self.rect = pygame.Rect(
        int(x - self.radius), int(y - self.radius), self.radius * 2, self.radius * 2
    )
    self.path_update_timer = random.randint(0, 30)

  def update(self, player, walls, bullets):
    dist_to_player = math.hypot(player.x - self.x, player.y - self.y)

    if self.type == "mage":
      # Mage keeps distance and shoots projectiles
      if dist_to_player < 300:
        # Move away or strafe
        angle = math.atan2(self.y - player.y, self.x - player.x)
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed
        self.move(dx, dy, walls)

      if self.shoot_cooldown > 0:
        self.shoot_cooldown -= 1
      else:
        if dist_to_player < 350:
          angle = math.atan2(player.y - self.y, player.x - self.x)
          bullets.append(
              Bullet(
                  self.x,
                  self.y,
                  math.cos(angle),
                  math.sin(angle),
                  4,
                  self.damage,
                  is_player=False,
              )
          )
          self.shoot_cooldown = 90
    else:
      # Melee rush logic
      if dist_to_player < 400:
        angle = math.atan2(player.y - self.y, player.x - self.x)
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed
        self.move(dx, dy, walls)

  def move(self, dx, dy, walls):
    self.x += dx
    self.rect.x = int(self.x - self.radius)
    for wall in walls:
      if self.rect.colliderect(wall):
        if dx > 0:
          self.rect.right = wall.left
        elif dx < 0:
          self.rect.left = wall.right
        self.x = self.rect.centerx

    self.y += dy
    self.rect.y = int(self.y - self.radius)
    for wall in walls:
      if self.rect.colliderect(wall):
        if dy > 0:
          self.rect.bottom = wall.top
        elif dy < 0:
          self.rect.top = wall.bottom
        self.y = self.rect.centery

  def draw(self, surface, camera):
    pos = camera.apply_point((int(self.x), int(self.y)))
    pygame.draw.circle(surface, self.color, pos, self.radius)
    pygame.draw.circle(surface, BLACK, pos, self.radius, 2)

    # Health bar above enemy
    hb_w = self.radius * 2
    hb_h = 4
    hp_pct = max(0, self.hp / self.max_hp)
    pygame.draw.rect(
        surface, RED, (pos[0] - hb_w // 2, pos[1] - self.radius - 10, hb_w, hb_h)
    )
    pygame.draw.rect(
        surface,
        GREEN,
        (
            pos[0] - hb_w // 2,
            pos[1] - self.radius - 10,
            int(hb_w * hp_pct),
            hb_h,
        ),
    )


class Room:

  def __init__(self, x, y, w, h):
    self.x = x
    self.y = y
    self.w = w
    self.h = h
    self.center = (x + w // 2, y + h // 2)

  def intersects(self, other):
    return (
        self.x < other.x + other.w
        and self.x + self.w > other.x
        and self.y < other.y + other.h
        and self.y + self.h > other.y
    )


class Dungeon:

  def __init__(self, width=80, height=60, tile_size=40):
    self.width = width
    self.height = height
    self.tile_size = tile_size
    self.tiles = [[1 for _ in range(height)] for _ in range(width)]
    self.rooms = []
    self.walls = []
    self.floors = []
    self.generate()

  def generate(self):
    self.tiles = [[1 for _ in range(self.height)] for _ in range(self.width)]
    self.rooms = []
    max_rooms = 15

    for _ in range(max_rooms):
      w = random.randint(6, 12)
      h = random.randint(6, 12)
      x = random.randint(1, self.width - w - 1)
      y = random.randint(1, self.height - h - 1)

      new_room = Room(x, y, w, h)
      failed = any(new_room.intersects(r) for r in self.rooms)

      if not failed:
        self.create_room(new_room)
        if self.rooms:
          prev_center = self.rooms[-1].center
          curr_center = new_room.center
          if random.random() < 0.5:
            self.create_h_tunnel(prev_center[0], curr_center[0], prev_center[1])
            self.create_v_tunnel(prev_center[1], curr_center[1], curr_center[0])
          else:
            self.create_v_tunnel(prev_center[1], curr_center[1], prev_center[0])
            self.create_h_tunnel(prev_center[0], curr_center[0], curr_center[1])
        self.rooms.append(new_room)

    self.build_collision_rects()

  def create_room(self, room):
    for x in range(room.x, room.x + room.w):
      for y in range(room.y, room.y + room.h):
        self.tiles[x][y] = 0

  def create_h_tunnel(self, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
      self.tiles[x][y] = 0

  def create_v_tunnel(self, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
      self.tiles[x][y] = 0

  def build_collision_rects(self):
    self.walls = []
    self.floors = []
    ts = self.tile_size
    for x in range(self.width):
      for y in range(self.height):
        rect = pygame.Rect(x * ts, y * ts, ts, ts)
        if self.tiles[x][y] == 1:
          self.walls.append(rect)
        else:
          self.floors.append(rect)


class Game:

  def __init__(self):
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Crawler - Advanced Python Game")
    self.clock = pygame.time.Clock()
    self.font = pygame.font.SysFont("Arial", 18)
    self.big_font = pygame.font.SysFont("Arial", 36, bold=True)
    self.reset_game()

  def reset_game(self):
    self.dungeon = Dungeon()
    spawn_room = self.dungeon.rooms[0]
    self.player = Player(
        spawn_room.center[0] * self.dungeon.tile_size,
        spawn_room.center[1] * self.dungeon.tile_size,
    )
    self.camera = Camera(
        self.dungeon.width * self.dungeon.tile_size,
        self.dungeon.height * self.dungeon.tile_size,
    )
    self.bullets = []
    self.enemies = []
    self.particles = []
    self.spawn_enemies()
    self.game_state = "PLAYING"
    self.level = 1

  def spawn_enemies(self):
    self.enemies = []
    for i, room in enumerate(self.dungeon.rooms):
      if i == 0:
        continue  # Skip player start room
      num_enemies = random.randint(1, 3)
      for _ in range(num_enemies):
        ex = (room.x + random.randint(1, room.w - 1)) * self.dungeon.tile_size
        ey = (room.y + random.randint(1, room.h - 1)) * self.dungeon.tile_size
        etype = random.choices(
            ["goblin", "orc", "mage"], weights=[0.6, 0.3, 0.1]
        )[0]
        self.enemies.append(Enemy(ex, ey, etype))

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
        if self.game_state == "GAME_OVER" and event.key == pygame.K_r:
          self.reset_game()

      if event.type == pygame.MOUSEBUTTONDOWN and self.game_state == "PLAYING":
        if event.button == 1 and self.player.shoot_cooldown == 0:
          mx, my = pygame.mouse.get_pos()
          # Convert screen mouse pos to world pos
          wx = mx - self.camera.camera.x
          wy = my - self.camera.camera.y
          angle = math.atan2(wy - self.player.y, wx - self.player.x)
          dx = math.cos(angle)
          dy = math.sin(angle)
          self.bullets.append(
              Bullet(
                  self.player.x,
                  self.player.y,
                  dx,
                  dy,
                  self.player.weapon_speed,
                  self.player.damage,
                  is_player=True,
              )
          )
          self.player.shoot_cooldown = 15

  def update(self):
    if self.game_state != "PLAYING":
      return

    keys = pygame.K_GET_PRESSED_EX if hasattr(pygame, "K_GET_PRESSED_EX") else {}
    keys = pygame.key.get_pressed()

    self.player.update(keys, self.dungeon.walls)
    self.camera.update(self.player)

    # Update Bullets
    for bullet in self.bullets[:]:
      is_hit = bullet.update(self.dungeon.walls)
      if is_hit:
        self.bullets.remove(bullet)
        for _ in range(4):
          self.particles.append(
              Particle(
                  bullet.x,
                  bullet.y,
                  YELLOW if bullet.is_player else PURPLE,
                  (random.uniform(-2, 2), random.uniform(-2, 2)),
                  15,
                  2,
              )
          )
        continue

      # Bullet collisions with entities
      if bullet.is_player:
        hit_enemy = None
        for enemy in self.enemies:
          if enemy.rect.collidepoint(bullet.x, bullet.y):
            hit_enemy = enemy
            break
        if hit_enemy:
          hit_enemy.hp -= bullet.damage
          if bullet in self.bullets:
            self.bullets.remove(bullet)
          for _ in range(6):
            self.particles.append(
                Particle(
                    bullet.x,
                    bullet.y,
                    RED,
                    (random.uniform(-3, 3), random.uniform(-3, 3)),
                    20,
                    3,
                )
            )
      else:
        # Enemy bullet hits player
        if self.player.rect.collidepoint(bullet.x, bullet.y):
          self.player.hp -= bullet.damage
          if bullet in self.bullets:
            self.bullets.remove(bullet)
          for _ in range(6):
            self.particles.append(
                Particle(
                    bullet.x,
                    bullet.y,
                    RED,
                    (random.uniform(-3, 3), random.uniform(-3, 3)),
                    20,
                    3,
                )
            )

    # Update Enemies
    for enemy in self.enemies[:]:
      enemy.update(self.player, self.dungeon.walls, self.bullets)
      if enemy.hp <= 0:
        self.enemies.remove(enemy)
        self.player.score += 100
        self.player.gold += random.randint(5, 15)
        for _ in range(12):
          self.particles.append(
              Particle(
                  enemy.x,
                  enemy.y,
                  GREEN,
                  (random.uniform(-4, 4), random.uniform(-4, 4)),
                  30,
                  4,
              )
          )
      elif enemy.rect.colliderect(self.player.rect):
        self.player.hp -= 0.5  # Contact damage

    # Update Particles
    for p in self.particles[:]:
      p.update()
      if p.lifetime <= 0:
        self.particles.remove(p)

    # Check Level Clear
    if len(self.enemies) == 0:
      self.level += 1
      self.dungeon.generate()
      spawn_room = self.dungeon.rooms[0]
      self.player.x = spawn_room.center[0] * self.dungeon.tile_size
      self.player.y = spawn_room.center[1] * self.dungeon.tile_size
      self.spawn_enemies()
      self.player.hp = min(self.player.max_hp, self.player.hp + 30)

    # Check Game Over
    if self.player.hp <= 0:
      self.game_state = "GAME_OVER"

  def draw(self):
    self.screen.fill(BLACK)

    # Draw Dungeon Floors
    for floor_rect in self.dungeon.floors:
      if self.camera.camera.colliderect(floor_rect):
        pygame.draw.rect(
            self.screen, DARK_GRAY, self.camera.apply(floor_rect)
        )

    # Draw Dungeon Walls
    for wall_rect in self.dungeon.walls:
      if self.camera.camera.colliderect(wall_rect):
        pygame.draw.rect(
            self.screen, LIGHT_GRAY, self.camera.apply(wall_rect)
        )
        pygame.draw.rect(
            self.screen, BLACK, self.camera.apply(wall_rect), 1
        )  # Outline

    # Draw Particles
    for p in self.particles:
      p.draw(self.screen, self.camera)

    # Draw Bullets
    for bullet in self.bullets:
      bullet.draw(self.screen, self.camera)

    # Draw Enemies
    for enemy in self.enemies:
      enemy.draw(self.screen, self.camera)

    # Draw Player
    self.player.draw(self.screen, self.camera)

    # Draw HUD / UI
    self.draw_hud()

    if self.game_state == "GAME_OVER":
      overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
      overlay.fill((0, 0, 0, 180))
      self.screen.blit(overlay, (0, 0))

      game_over_surf = self.big_font.read = self.big_font.render(
          "GAME OVER", True, RED
      )
      self.screen.blit(
          game_over_surf,
          (
              SCREEN_WIDTH // 2 - game_over_surf.get_width() // 2,
              SCREEN_HEIGHT // 2 - 50,
          ),
      )

      restart_surf = self.font.render(
          "Press 'R' to Restart or 'ESC' to Quit", True, WHITE
      )
      self.screen.blit(
          restart_surf,
          (
              SCREEN_WIDTH // 2 - restart_surf.get_width() // 2,
              SCREEN_HEIGHT // 2 + 10,
          ),
      )

    pygame.display.flip()

  def draw_hud(self):
    # Health bar
    bar_w, bar_h = 200, 20
    hp_pct = max(0, self.player.hp / self.player.max_hp)
    pygame.draw.rect(self.screen, DARK_GRAY, (20, 20, bar_w, bar_h))
    pygame.draw.rect(self.screen, RED, (20, 20, int(bar_w * hp_pct), bar_h))
    pygame.draw.rect(self.screen, WHITE, (20, 20, bar_w, bar_h), 2)

    hp_text = self.font.render(
        f"HP: {int(self.player.hp)} / {self.player.max_hp}", True, WHITE
    )
    self.screen.blit(hp_text, (30, 22))

    # Stats text
    score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
    gold_text = self.font.render(f"Gold: {self.player.gold}", True, YELLOW)
    level_text = self.font.render(f"Dungeon Level: {self.level}", True, GREEN)
    enemies_text = self.font.render(
        f"Enemies Left: {len(self.enemies)}", True, ORANGE
    )

    self.screen.blit(score_text, (20, 55))
    self.screen.blit(gold_text, (20, 80))
    self.screen.blit(level_text, (20, 105))
    self.screen.blit(enemies_text, (20, 130))

    controls_text = self.font.render(
        "WASD: Move | Left Click: Shoot", True, LIGHT_GRAY
    )
    self.screen.blit(controls_text, (20, SCREEN_HEIGHT - 35))


if __name__ == "__main__":
  game = Game()
  game.run()