import pygame
import sys
import random
import os

# --- NEW: PYINSTALLER PATH RESOLVER ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not running as an .exe, use the normal current directory
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- CONSTANTS ---
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

GRAVITY = 0.5
FLAP_STRENGTH = -8

PIPE_WIDTH = 50
PIPE_GAP = 150
PIPE_VELOCITY = 3
SPAWN_RATE = 1500

SKY_BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)

# --- UPDATED TO USE resource_path ---
def load_image(filename, size, fallback_color):
    # Use our new helper to find the exact file location
    path = resource_path(os.path.join("assets", "sprites", filename))
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, size)
        return img
    except FileNotFoundError:
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

class DummySound:
    def play(self): pass

# --- UPDATED TO USE resource_path ---
def load_sound(filename):
    path = resource_path(os.path.join("assets", "audio", filename))
    try:
        return pygame.mixer.Sound(path)
    except (FileNotFoundError, pygame.error):
        return DummySound()

class Bird:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 34, 24)
        self.velocity = 0
        self.image = load_image("bird.png", (self.rect.width, self.rect.height), YELLOW)
        self.jump_sound = load_sound("jump.wav")

    def flap(self):
        self.velocity = FLAP_STRENGTH
        self.jump_sound.play()

    def update(self):
        self.velocity += GRAVITY
        self.rect.y += self.velocity

    def draw(self, screen):
        # --- NEW: BIRD ROTATION ---
        # 1. Calculate the angle based on velocity.
        # Multiplying by -3 makes the rotation sensitive to speed.
        angle = self.velocity * -3 
        
        # 2. Limit (clamp) the angle so it doesn't spin completely upside down
        # Max pointing up: 25 degrees. Max pointing down: -90 degrees.
        angle = max(-90, min(angle, 25))
        
        # 3. Rotate the image
        rotated_image = pygame.transform.rotate(self.image, angle)
        
        # 4. Get the new bounding box and center it on the original bird's position
        rotated_rect = rotated_image.get_rect(center=self.rect.center)
        
        # 5. Draw the rotated image
        screen.blit(rotated_image, rotated_rect)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.gap_y = random.randint(150, SCREEN_HEIGHT - 150)
        top_height = self.gap_y - (PIPE_GAP // 2)
        self.top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, top_height)
        bottom_y = self.gap_y + (PIPE_GAP // 2)
        bottom_height = SCREEN_HEIGHT - bottom_y
        self.bottom_rect = pygame.Rect(self.x, bottom_y, PIPE_WIDTH, bottom_height)
        self.passed = False
        self.bottom_image = load_image("pipe.png", (PIPE_WIDTH, bottom_height), GREEN)
        self.top_image = load_image("pipe.png", (PIPE_WIDTH, top_height), GREEN)
        self.top_image = pygame.transform.flip(self.top_image, False, True)

    def update(self):
        self.x -= PIPE_VELOCITY
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self, screen):
        screen.blit(self.top_image, self.top_rect)
        screen.blit(self.bottom_image, self.bottom_rect)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird - Pro Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_large = pygame.font.SysFont('Arial', 48, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 24, bold=True)
        
        # Background Setup
        self.bg_image = load_image("bg.png", (SCREEN_WIDTH, SCREEN_HEIGHT), SKY_BLUE)
        
        # --- NEW: BACKGROUND SCROLLING VARIABLES ---
        self.bg_scroll = 0
        self.bg_scroll_speed = 1 # Scrolling slower than pipes creates a cool 3D depth effect!
        
        self.score_sound = load_sound("score.wav")
        self.hit_sound = load_sound("hit.wav")
        self.SPAWNPIPE = pygame.USEREVENT
        pygame.time.set_timer(self.SPAWNPIPE, SPAWN_RATE)
        self.game_state = "START" 
        self.high_score = self.load_high_score()
        self.reset_game()

    def load_high_score(self):
        path = os.path.join("data", "highscore.txt")
        try:
            with open(path, "r") as file:
                return int(file.read())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "highscore.txt")
        with open(path, "w") as file:
            file.write(str(self.high_score))

    def reset_game(self):
        self.bird = Bird(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
        self.pipes = []
        self.score = 0

    def trigger_game_over(self):
        self.hit_sound.play()
        self.game_state = "GAME_OVER"
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.game_state in ["START", "PLAYING"]:
                    self.game_state = "PLAYING"
                    self.bird.flap()
                elif self.game_state == "GAME_OVER":
                    self.reset_game()
                    self.game_state = "PLAYING"
                    self.bird.flap()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                if self.game_state in ["START", "PLAYING"]:
                    self.game_state = "PLAYING"
                    self.bird.flap()
                elif self.game_state == "GAME_OVER":
                    self.reset_game()
                    self.game_state = "PLAYING"
                    self.bird.flap()
                    
            if event.type == self.SPAWNPIPE and self.game_state == "PLAYING":
                new_pipe = Pipe(SCREEN_WIDTH)
                self.pipes.append(new_pipe)

    def check_collisions(self):
        if self.bird.rect.bottom >= SCREEN_HEIGHT or self.bird.rect.top <= 0:
            self.trigger_game_over()
            return
        for pipe in self.pipes:
            if self.bird.rect.colliderect(pipe.top_rect) or self.bird.rect.colliderect(pipe.bottom_rect):
                self.trigger_game_over()
                return

    def update(self):
        # --- NEW: BACKGROUND SCROLLING LOGIC ---
        # We scroll the background on the Start Screen AND while Playing!
        if self.game_state in ["START", "PLAYING"]:
            self.bg_scroll -= self.bg_scroll_speed
            # If the first image has scrolled completely off screen, reset it!
            if abs(self.bg_scroll) >= SCREEN_WIDTH:
                self.bg_scroll = 0

        if self.game_state == "PLAYING":
            self.bird.update()
            
            for pipe in self.pipes:
                pipe.update()
                if pipe.top_rect.right < self.bird.rect.left and not pipe.passed:
                    self.score += 1
                    pipe.passed = True
                    self.score_sound.play()
                
            self.pipes = [pipe for pipe in self.pipes if pipe.top_rect.right > 0]
            self.check_collisions()

    def draw_text(self, text, font, text_col, x, y):
        shadow = font.render(text, True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(x+2, y+2))
        self.screen.blit(shadow, shadow_rect)
        img = font.render(text, True, text_col)
        rect = img.get_rect(center=(x, y))
        self.screen.blit(img, rect)

    def draw(self):
        # --- NEW: DRAWING THE SCROLLING BACKGROUND ---
        # Draw the image twice side-by-side to create the infinite loop
        self.screen.blit(self.bg_image, (self.bg_scroll, 0))
        self.screen.blit(self.bg_image, (self.bg_scroll + SCREEN_WIDTH, 0))
        
        for pipe in self.pipes:
            pipe.draw(self.screen)
            
        self.bird.draw(self.screen) 
        
        if self.game_state == "START":
            self.draw_text("FLAPPY BIRD", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
            self.draw_text("Press SPACE to Start", self.font_small, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
            
        elif self.game_state == "PLAYING":
            self.draw_text(str(self.score), self.font_large, WHITE, SCREEN_WIDTH // 2, 50)
            
        elif self.game_state == "GAME_OVER":
            self.draw_text("GAME OVER", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 - 50)
            self.draw_text(f"Score: {self.score}", self.font_large, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)
            self.draw_text(f"Best: {self.high_score}", self.font_small, YELLOW, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
            self.draw_text("Press SPACE to Restart", self.font_small, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()