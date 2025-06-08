import pygame
import random
import asyncio
import platform
from math import floor

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trúc Xanh Music")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
HIGHLIGHT = (200, 200, 200)

# Game settings
FPS = 60
CARD_WIDTH, CARD_HEIGHT = 60, 60
CARD_MARGIN = 10
NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
NOTE_COLORS = {
    'C': (255, 0, 0), 'D': (255, 165, 0), 'E': (255, 255, 0),
    'F': (0, 128, 0), 'G': (0, 0, 255), 'A': (75, 0, 130), 'B': (238, 130, 238)
}

# Font
font = pygame.font.SysFont('arial', 36)

# Sound generation
def create_note_sound(frequency, duration=0.5, sample_rate=44100):
    """Generate sound for a note frequency."""
    import numpy as np
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((sound, sound)))

# Dictionary of pre-generated note sounds
NOTE_SOUNDS = {
    'C': create_note_sound(261.63),
    'D': create_note_sound(293.66),
    'E': create_note_sound(329.63),
    'F': create_note_sound(349.23),
    'G': create_note_sound(392.00),
    'A': create_note_sound(440.00),
    'B': create_note_sound(493.88)
}

class Card:
    def __init__(self, note, x, y):
        """Initialize a card with a note and position."""
        self.note = note
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.is_flipped = False
        self.is_matched = False

class Button:
    def __init__(self, text, x, y, width, height):
        """Initialize a menu button."""
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.hovered = False

    def draw(self, surface):
        """Draw the button on the screen."""
        color = HIGHLIGHT if self.hovered else WHITE
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text_surface = font.render(self.text, True, BLACK)
        surface.blit(text_surface, (self.rect.x + (self.rect.width - text_surface.get_width()) // 2,
                                  self.rect.y + (self.rect.height - text_surface.get_height()) // 2))

    def check_hover(self, pos):
        """Check if the mouse is hovering over the button."""
        self.hovered = self.rect.collidepoint(pos)

class Game:
    def __init__(self):
        """Initialize game state and UI buttons."""
        self.state = 'menu'
        self.grid_size = None
        self.cards = []
        self.flipped_cards = []
        self.scores = {1: 0}
        self.waiting = False
        self.wait_start_time = 0
        self.wait_duration = 1000
        self.message = ""
        self.message_timer = 0
        self.buttons = [
            Button("Start 25 Pairs", WIDTH // 2 - 100, 300, 200, 50),
            Button("Start 15 Pairs", WIDTH // 2 - 100, 360, 200, 50)
        ]

    def setup_game(self, grid_size):
        """Set up game grid based on number of card pairs."""
        self.grid_size = grid_size
        self.cards = []
        self.flipped_cards = []
        self.scores = {1: 0}
        self.state = 'playing'

        pairs = grid_size // 2
        selected_notes = random.choices(NOTES, k=pairs)
        card_notes = selected_notes * 2
        random.shuffle(card_notes)

        rows = 5
        cols = grid_size // 5
        start_x = (WIDTH - (cols * (CARD_WIDTH + CARD_MARGIN) - CARD_MARGIN)) // 2
        start_y = (HEIGHT - (rows * (CARD_HEIGHT + CARD_MARGIN) - CARD_MARGIN)) // 2

        for i in range(rows):
            for j in range(cols):
                idx = i * cols + j
                if idx < len(card_notes):
                    x = start_x + j * (CARD_WIDTH + CARD_MARGIN)
                    y = start_y + i * (CARD_HEIGHT + CARD_MARGIN)
                    self.cards.append(Card(card_notes[idx], x, y))

    def draw(self):
        """Render the game screen based on state."""
        screen.fill(WHITE)
        if self.state == 'menu':
            title = font.render("Trúc Xanh Music", True, BLACK)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
            for button in self.buttons:
                button.draw(screen)
        elif self.state == 'playing':
            for card in self.cards:
                if card.is_matched or card.is_flipped:
                    pygame.draw.rect(screen, NOTE_COLORS[card.note], card.rect)
                    text = font.render(card.note, True, BLACK)
                    screen.blit(text, (card.rect.x + 20, card.rect.y + 20))
                else:
                    pygame.draw.rect(screen, GRAY, card.rect)
            score_text = font.render(f"Score: {self.scores[1]}", True, BLACK)
            screen.blit(score_text, (10, 10))
            if self.message:
                msg_surface = font.render(self.message, True, BLACK)
                screen.blit(msg_surface, (WIDTH // 2 - msg_surface.get_width() // 2, HEIGHT - 50))
        elif self.state == 'game_over':
            text = font.render(f"Game Over! Score: {self.scores[1]}", True, BLACK)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            restart = font.render("Press [R] to Restart", True, BLACK)
            screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 50))

    def handle_click(self, pos):
        """Handle mouse click depending on game state."""
        if self.state == 'menu':
            for button in self.buttons:
                if button.rect.collidepoint(pos):
                    if "25" in button.text:
                        self.setup_game(50)
                    elif "15" in button.text:
                        self.setup_game(30)
        elif self.state == 'playing' and not self.waiting:
            for card in self.cards:
                if card.rect.collidepoint(pos) and not card.is_flipped and not card.is_matched:
                    card.is_flipped = True
                    NOTE_SOUNDS[card.note].play()
                    self.flipped_cards.append(card)
                    if len(self.flipped_cards) == 2:
                        self.check_match()

    def check_match(self):
        """Check if two flipped cards match."""
        card1, card2 = self.flipped_cards
        if card1.note == card2.note:
            card1.is_matched = card2.is_matched = True
            self.scores[1] += 1
            self.flipped_cards = []
            self.message = "Match!"
            self.message_timer = pygame.time.get_ticks()
            if all(card.is_matched for card in self.cards):
                self.state = 'game_over'
        else:
            self.waiting = True
            self.wait_start_time = pygame.time.get_ticks()
            self.message = "No Match!"
            self.message_timer = pygame.time.get_ticks()

    def update(self):
        """Update game logic, including card flip timing."""
        if self.waiting and pygame.time.get_ticks() - self.wait_start_time > self.wait_duration:
            for card in self.flipped_cards:
                card.is_flipped = False
            self.flipped_cards = []
            self.waiting = False
        if self.message and pygame.time.get_ticks() - self.message_timer > 1000:
            self.message = ""

game = Game()

# Main game loop
async def main():
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEMOTION:
                if game.state == 'menu':
                    for button in game.buttons:
                        button.check_hover(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(event.pos)
            if event.type == pygame.KEYDOWN:
                if game.state == 'game_over' and event.key == pygame.K_r:
                    game.state = 'menu'
                    game.grid_size = None

        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())