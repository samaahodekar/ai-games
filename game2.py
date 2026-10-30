import json
import os
import random
import sys
import pygame

# Initialize Pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Colors
DARK_BG = (20, 24, 33)
CARD_BG = (32, 38, 52)
WHITE = (240, 244, 248)
LIGHT_GRAY = (140, 150, 170)
BLUE = (67, 97, 238)
BLUE_HOVER = (72, 149, 239)
GREEN = (76, 201, 240)
RED = (247, 37, 133)
YELLOW = (252, 191, 73)


class Button:

  def __init__(self, x, y, width, height, text, font, bg_color, hover_color):
    self.rect = pygame.Rect(x, y, width, height)
    self.text = text
    self.font = font
    self.bg_color = bg_color
    self.hover_color = hover_color
    self.is_hovered = False

  def draw(self, surface):
    color = self.hover_color if self.is_hovered else self.bg_color
    pygame.draw.rect(surface, color, self.rect, border_radius=12)
    pygame.draw.rect(
        surface, LIGHT_GRAY, self.rect, 2, border_radius=12
    )  # Border

    text_surf = self.font.render(self.text, True, WHITE)
    text_rect = text_surf.get_rect(center=self.rect.center)
    surface.blit(text_surf, text_rect)

  def check_hover(self, pos):
    self.is_hovered = self.rect.collidepoint(pos)

  def is_clicked(self, pos, event):
    return (
        event.type == pygame.MOUSEBUTTONDOWN
        and event.button == 1
        and self.rect.collidepoint(pos)
    )


class QuizGame:

  def __init__(self):
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ultimate Trivia Quiz Game")
    self.clock = pygame.time.Clock()

    # Fonts
    self.font_sm = pygame.font.SysFont("Arial", 20)
    self.font_md = pygame.font.SysFont("Arial", 24, bold=True)
    self.font_lg = pygame.font.SysFont("Arial", 36, bold=True)
    self.font_title = pygame.font.SysFont("Arial", 48, bold=True)

    self.load_questions()
    self.state = "MENU"  # MENU, CATEGORY, PLAYING, GAMEOVER, HIGHSCORES
    self.current_category = None
    self.questions = []
    self.current_q_index = 0
    self.score = 0
    self.streak = 0
    self.timer = 15.0  # 15 seconds per question
    self.selected_answer = None
    self.answer_timer = 0  # Pause to show correct/incorrect color
    self.high_scores = self.load_high_scores()

    self.setup_menu_buttons()

  def load_questions(self):
    # Sample robust question database by categories
    self.database = {
        "Computer Science": [
            {
                "q": "What does CPU stand for?",
                "options": [
                    "Central Processing Unit",
                    "Computer Personal Unit",
                    "Central Program Utility",
                    "Control Processing Unit",
                ],
                "answer": 0,
            },
            {
                "q": "Which data structure uses LIFO (Last In, First Out)?",
                "options": ["Queue", "Stack", "Array", "Tree"],
                "answer": 1,
            },
            {
                "q": "What is the time complexity of binary search?",
                "options": ["O(n)", "O(n log n)", "O(log n)", "O(1)"],
                "answer": 2,
            },
            {
                "q": "Who is often considered the first computer programmer?",
                "options": [
                    "Alan Turing",
                    "Charles Babbage",
                    "Ada Lovelace",
                    "Bill Gates",
                ],
                "answer": 2,
            },
        ],
        "Science & Space": [
            {
                "q": "What planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "answer": 1,
            },
            {
                "q": "What is the chemical symbol for Gold?",
                "options": ["Ag", "Fe", "Au", "Pb"],
                "answer": 2,
            },
            {
                "q": "How long does light from the Sun take to reach Earth?",
                "options": [
                    "8 seconds",
                    "8 minutes",
                    "1 hour",
                    "24 hours",
                ],
                "answer": 1,
            },
            {
                "q": "What gas makes up the majority of Earth's atmosphere?",
                "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
                "answer": 2,
            },
        ],
        "History & Geography": [
            {
                "q": "In which year did the Titanic sink?",
                "options": ["1905", "1912", "1923", "1898"],
                "answer": 1,
            },
            {
                "q": "What is the capital city of Australia?",
                "options": ["Sydney", "Melbourne", "Canberra", "Brisbane"],
                "answer": 2,
            },
            {
                "q": "Who painted the Mona Lisa?",
                "options": [
                    "Vincent van Gogh",
                    "Pablo Picasso",
                    "Leonardo da Vinci",
                    "Claude Monet",
                ],
                "answer": 2,
            },
            {
                "q": "Which empire built the ancient city of Machu Picchu?",
                "options": ["Roman", "Inca", "Aztec", "Maya"],
                "answer": 1,
            },
        ],
    }

  def load_high_scores(self):
    if os.path.exists("highscores.json"):
      try:
        with open("highscores.json", "r") as f:
          return json.load(f)
      except:
        return {}
    return {}

  def save_high_scores(self):
    with open("highscores.json", "w") as f:
      json.dump(self.high_scores, f)

  def setup_menu_buttons(self):
    self.menu_buttons = [
        Button(
            SCREEN_WIDTH // 2 - 150,
            300,
            300,
            50,
            "Play Game",
            self.font_md,
            BLUE,
            BLUE_HOVER,
        ),
        Button(
            SCREEN_WIDTH // 2 - 150,
            370,
            300,
            50,
            "High Scores",
            self.font_md,
            CARD_BG,
            BLUE,
        ),
        Button(
            SCREEN_WIDTH // 2 - 150,
            440,
            300,
            50,
            "Quit",
            self.font_md,
            CARD_BG,
            RED,
        ),
    ]

  def setup_category_buttons(self):
    self.cat_buttons = []
    y = 280
    for cat in self.database.keys():
      self.cat_buttons.append(
          Button(
              SCREEN_WIDTH // 2 - 200,
              y,
              400,
              50,
              cat,
              self.font_md,
              CARD_BG,
              BLUE,
          )
      )
      y += 70
    self.cat_buttons.append(
        Button(
            SCREEN_WIDTH // 2 - 200,
            y + 20,
            400,
            50,
            "Back to Menu",
            self.font_md,
            DARK_BG,
            LIGHT_GRAY,
        )
    )

  def setup_gameplay_buttons(self):
    self.choice_buttons = []
    y = 380
    for i in range(4):
      self.choice_buttons.append(
          Button(
              SCREEN_WIDTH // 2 - 300,
              y,
              600,
              60,
              "",
              self.font_md,
              CARD_BG,
              BLUE_HOVER,
          )
      )
      y += 80

  def start_quiz(self, category):
    self.current_category = category
    self.questions = list(self.database[category])
    random.shuffle(self.questions)
    self.current_q_index = 0
    self.score = 0
    self.streak = 0
    self.setup_gameplay_buttons()
    self.load_current_question()
    self.state = "PLAYING"

  def load_current_question(self):
    if self.current_q_index < len(self.questions):
      q_data = self.questions[self.current_q_index]
      for i, btn in enumerate(self.choice_buttons):
        btn.text = f"{chr(65+i)}. {q_data['options'][i]}"
        btn.bg_color = CARD_BG
      self.timer = 15.0
      self.selected_answer = None
      self.answer_timer = 0
    else:
      # Quiz completed
      self.state = "GAMEOVER"
      if (
          self.current_category not in self.high_scores
          or self.score > self.high_scores[self.current_category]
      ):
        self.high_scores[self.current_category] = self.score
        self.save_high_scores()

  def run(self):
    while True:
      dt = self.clock.tick(FPS) / 1000.0
      mouse_pos = pygame.mouse.get_pos()

      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          pygame.quit()
          sys.exit()

        if self.state == "MENU":
          for btn in self.menu_buttons:
            if btn.is_clicked(mouse_pos, event):
              if btn.text == "Play Game":
                self.setup_category_buttons()
                self.state = "CATEGORY"
              elif btn.text == "High Scores":
                self.state = "HIGHSCORES"
              elif btn.text == "Quit":
                pygame.quit()
                sys.exit()

        elif self.state == "CATEGORY":
          for btn in self.cat_buttons:
            if btn.is_clicked(mouse_pos, event):
              if btn.text == "Back to Menu":
                self.state = "MENU"
              else:
                self.start_quiz(btn.text)

        elif self.state == "PLAYING":
          if self.answer_timer == 0:
            for i, btn in enumerate(self.choice_buttons):
              if btn.is_clicked(mouse_pos, event):
                self.selected_answer = i
                correct_idx = self.questions[self.current_q_index]["answer"]
                if self.selected_answer == correct_idx:
                  btn.bg_color = GREEN
                  self.score += int(100 + (self.timer * 5) + (self.streak * 10))
                  self.streak += 1
                else:
                  btn.bg_color = RED
                  self.choice_buttons[correct_idx].bg_color = GREEN
                  self.streak = 0
                self.answer_timer = 1.5  # Wait 1.5s before next question

        elif self.state == "GAMEOVER" or self.state == "HIGHSCORES":
          if event.type == pygame.MOUSEBUTTONDOWN:
            self.state = "MENU"

      # Update logic
      if self.state == "MENU":
        for btn in self.menu_buttons:
          btn.check_hover(mouse_pos)
      elif self.state == "CATEGORY":
        for btn in self.cat_buttons:
          btn.check_hover(mouse_pos)
      elif self.state == "PLAYING":
        if self.answer_timer > 0:
          self.answer_timer -= dt
          if self.answer_timer <= 0:
            self.current_q_index += 1
            self.load_current_question()
        else:
          self.timer -= dt
          if self.timer <= 0:
            # Timeout counts as wrong answer
            correct_idx = self.questions[self.current_q_index]["answer"]
            self.choice_buttons[correct_idx].bg_color = GREEN
            self.streak = 0
            self.answer_timer = 1.5
          for btn in self.choice_buttons:
            btn.check_hover(mouse_pos)

      # Draw logic
      self.draw(mouse_pos)

  def draw(self, mouse_pos):
    self.screen.fill(DARK_BG)

    if self.state == "MENU":
      title = self.font_title.render("ULTIVIVIZ TRIVIA", True, WHITE)
      self.screen.blit(
          title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 160)
      )
      for btn in self.menu_buttons:
        btn.draw(self.screen)

    elif self.state == "CATEGORY":
      title = self.font_lg.render("Select a Category", True, WHITE)
      self.screen.blit(
          title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180)
      )
      for btn in self.cat_buttons:
        btn.draw(self.screen)

    elif self.state == "PLAYING":
      q_data = self.questions[self.current_q_index]

      # Header info
      cat_surf = self.font_sm.render(
          f"Category: {self.current_category}", True, LIGHT_GRAY
      )
      progress_surf = self.font_sm.render(
          f"Question {self.current_q_index + 1}/{len(self.questions)}",
          True,
          LIGHT_GRAY,
      )
      score_surf = self.font_md.render(f"Score: {self.score}", True, YELLOW)
      streak_surf = self.font_sm.render(
          f"Streak: {self.streak}x 🔥", True, GREEN
      )

      self.screen.blit(cat_surf, (60, 40))
      self.screen.blit(progress_surf, (SCREEN_WIDTH - 200, 40))
      self.screen.blit(score_surf, (60, 80))
      self.screen.blit(streak_surf, (SCREEN_WIDTH - 200, 80))

      # Timer bar
      bar_width = 880
      bar_height = 10
      bar_x = 72
      bar_y = 130
      pygame.draw.rect(
          self.screen,
          CARD_BG,
          (bar_x, bar_y, bar_width, bar_height),
          border_radius=5,
      )
      fill_width = int(bar_width * (max(0.0, self.timer) / 15.0))
      timer_color = GREEN if self.timer > 5 else RED
      if fill_width > 0:
        pygame.draw.rect(
            self.screen,
            timer_color,
            (bar_x, bar_y, fill_width, bar_height),
            border_radius=5,
        )

      # Question box
      q_surf = self.font_lg.render(q_data["q"], True, WHITE)
      q_rect = q_surf.get_rect(
          center=(SCREEN_WIDTH // 2, 260)
      )  # Adjusted for spacing
      self.screen.blit(q_surf, q_rect)

      # Choices
      for btn in self.choice_buttons:
        btn.draw(self.screen)

    elif self.state == "GAMEOVER":
      title = self.font_title.render("Quiz Complete!", True, GREEN)
      score_text = self.font_lg.render(
          f"Final Score: {self.score}", True, YELLOW
      )
      info = self.font_sm.render("Click anywhere to return to menu", True, LIGHT_GRAY)

      self.screen.blit(
          title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 240)
      )
      self.screen.blit(
          score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 340)
      )
      self.screen.blit(
          info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 440)
      )

    elif self.state == "HIGHSCORES":
      title = self.font_lg.render("High Scores", True, WHITE)
      self.screen.blit(
          title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150)
      )

      y = 240
      if not self.high_scores:
        no_score = self.font_md.render("No high scores recorded yet!", True, LIGHT_GRAY)
        self.screen.blit(
            no_score, (SCREEN_WIDTH // 2 - no_score.get_width() // 2, y)
        )
      else:
        for cat, sc in self.high_scores.items():
          txt = self.font_md.render(f"{cat}: {sc} pts", True, YELLOW)
          self.screen.blit(txt, (SCREEN_WIDTH // 2 - 200, y))
          y += 50

      back_info = self.font_sm.render("Click anywhere to return to menu", True, LIGHT_GRAY)
      self.screen.blit(
          back_info, (SCREEN_WIDTH // 2 - back_info.get_width() // 2, 550)
      )

    pygame.display.flip()


if __name__ == "__main__":
  game = QuizGame()
  game.run()