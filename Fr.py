import pygame
import sys
import random
from pygame import USEREVENT

pygame.init()
pygame.mixer.init()

# Constants and Configuration
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
JUMP_POWER = -12
PLAYER_SPEED = 5
PLATFORM_WIDTH = 100
PLATFORM_HEIGHT = 20
INITIAL_PLATFORMS = 6  # Fewer initial platforms
MIN_GAP = 50
MAX_GAP = 100
POWER_UP_SPAWN_RATE = 5000  # milliseconds
SCORE_THRESHOLD = 500  # points needed for advanced features
POWER_UP_TYPES = ["double_jump", "speed_boost"]

# Color scheme
TEXT_COLOR = (75, 75, 75)              # Dark pastel gray for text
BUTTON_COLOR = (173, 216, 230)         # Light blue pastel
BUTTON_HOVER_COLOR = (176, 224, 230)   # Slightly lighter blue pastel
OVERLAY_COLOR = (255, 255, 255, 200)   # Translucent white overlay
SCORE_BG_COLOR = (0, 0, 0, 150)        # Semi-transparent black for score background
POWER_UP_COLOR = (255, 215, 0)         # Gold for power-ups

# Setup Display and Load Assets
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Castle Leap")

# Load backgrounds and assets
menu_bg = pygame.image.load("last.bg.jpeg")
menu_bg = pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
game_bg = pygame.image.load("Grey_Brick_Wallpaper.png")
game_bg = pygame.transform.scale(game_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
player_img = pygame.image.load("Tara.png")
platform_img = pygame.image.load("platform_img.png")
platform_img = pygame.transform.scale(platform_img, (PLATFORM_WIDTH, PLATFORM_HEIGHT))

# Load sounds and music
jump_sound = pygame.mixer.Sound("jump.wav")
pygame.mixer.music.load("Adventure.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# Load custom font
try:
    title_font = pygame.font.Font("Press_Start_2P.ttf", 48)
except:
    title_font = pygame.font.Font(None, 48)

class Button:
    def __init__(self, text, x, y, width, height):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.hover = False

    def draw(self, surface):
        color = BUTTON_HOVER_COLOR if self.hover else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        try:
            btn_font = pygame.font.Font("Press_Start_2P.ttf", 24)
        except:
            btn_font = pygame.font.Font(None, 24)
        text_surf = btn_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_y = 0
        self.on_ground = True  # starts on a platform
        self.prev_bottom = self.rect.bottom
        self.jump_cooldown = 0
        self.can_double_jump = False
        self.power_ups = []
        self.last_landed_platform = None  # to track landing for scoring

    def update(self):
        keys = pygame.key.get_pressed()
        
        # Horizontal movement on user input
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED
            
        # Keep player within horizontal bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            
        # Store previous bottom for collision detection
        self.prev_bottom = self.rect.bottom
        
        # Handle jumping when on ground and SPACE is pressed.
        # Clear last_landed_platform so landing on a new one counts.
        if keys[pygame.K_SPACE] and self.on_ground and self.jump_cooldown <= 0:
            self.vel_y = JUMP_POWER
            self.on_ground = False
            self.last_landed_platform = None
            jump_sound.play()
            self.jump_cooldown = 10
            
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
            
        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        # Reset on_ground; collision will set it to True if landing.
        self.on_ground = False

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = platform_img
        self.rect = self.image.get_rect(topleft=(x, y))

class MovingPlatform(Platform):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 2
        self.direction = 1
        self.range = 200
        self.start_x = x  # store initial x position
        
    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.x > self.start_x + self.range // 2:
            self.direction = -1
        elif self.rect.x < self.start_x - self.range // 2:
            self.direction = 1

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_up_type="double_jump"):
        super().__init__()
        self.type = power_up_type
        self.image = pygame.Surface((20, 20))
        self.image.fill(POWER_UP_COLOR)
        self.rect = self.image.get_rect(center=(x, y))
        self.effect_duration = 10000
        
    def activate(self, player):
        if self.type == "double_jump":
            player.can_double_jump = True
        elif self.type == "speed_boost":
            global PLAYER_SPEED
            PLAYER_SPEED *= 1.5
            pygame.time.set_timer(USEREVENT + 1, self.effect_duration, True)

def show_story():
    # A longer, simple, and larger medieval tale (10 lines)
    story_lines = [
        "Welcome to Castle Leap!",
        "Jump from platform to platform,",
        "Climb high and reach the sky.",
        "Your adventure starts right here.",
        "Find magic and mystery on your way.",
        "Face each challenge with a brave heart.",
        "Every jump is a new beginning.",
        "Leap with joy and courage.",
        "Good luck, mighty jumper!",
        "Press X to start your quest!"
    ]
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))
    close_btn = Button("X", SCREEN_WIDTH - 60, 20, 40, 40)
    try:
        story_font = pygame.font.Font("Press_Start_2P.ttf", 30)
    except:
        story_font = pygame.font.Font(None, 30)
    y = 40
    for line in story_lines:
        text_surf = story_font.render(line, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y))
        screen.blit(text_surf, text_rect)
        y += 40
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if close_btn.rect.collidepoint(event.pos):
                    return
        mouse_pos = pygame.mouse.get_pos()
        close_btn.hover = close_btn.rect.collidepoint(mouse_pos)
        close_btn.draw(screen)
        pygame.display.update()

def show_how_to_play():
    instructions = [
        "How to Play:",
        "",
        "Left/Right Arrow Keys - Move",
        "Space - Jump",
        "",
        "Land on platforms to score:",
        "10 points & 15 meters per jump.",
        "Avoid falling off the bottom.",
        "",
        "Press X to return."
    ]
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))
    close_btn = Button("X", SCREEN_WIDTH - 60, 20, 40, 40)
    try:
        small_font = pygame.font.Font("Press_Start_2P.ttf", 20)
    except:
        small_font = pygame.font.Font(None, 20)
    y = 100
    for line in instructions:
        text_surf = small_font.render(line, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y))
        screen.blit(text_surf, text_rect)
        y += 30
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if close_btn.rect.collidepoint(event.pos):
                    return
        mouse_pos = pygame.mouse.get_pos()
        close_btn.hover = close_btn.rect.collidepoint(mouse_pos)
        close_btn.draw(screen)
        pygame.display.update()

def main_menu():
    screen.blit(menu_bg, (0, 0))
    title_text = title_font.render("Castle Leap", True, TEXT_COLOR)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
    screen.blit(title_text, title_rect)
    pygame.display.update()
    
    show_story()
    
    start_btn = Button("Start Quest", SCREEN_WIDTH // 2 - 100, 300, 200, 50)
    howto_btn = Button("How to Play", SCREEN_WIDTH // 2 - 100, 380, 200, 50)
    
    while True:
        screen.blit(menu_bg, (0, 0))
        screen.blit(title_text, title_rect)
        mouse_pos = pygame.mouse.get_pos()
        start_btn.hover = start_btn.rect.collidepoint(mouse_pos)
        howto_btn.hover = howto_btn.rect.collidepoint(mouse_pos)
        start_btn.draw(screen)
        howto_btn.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.rect.collidepoint(event.pos):
                    return "start"
                if howto_btn.rect.collidepoint(event.pos):
                    show_how_to_play()
        pygame.display.update()

def game_over_screen(points, meters):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))
    
    if points < 100:
        message = "Novice Jumper! Keep practicing!"
    elif points < 300:
        message = "Getting the hang of it! Nice try!"
    elif points < 500:
        message = "You're improving! Almost there!"
    elif points < 1000:
        message = "Experienced jumper! You've got this!"
    else:
        message = "Master jumper! Amazing score!"
    
    try:
        over_font = pygame.font.Font("Press_Start_2P.ttf", 48)
        message_font = pygame.font.Font("Press_Start_2P.ttf", 24)
    except:
        over_font = pygame.font.Font(None, 48)
        message_font = pygame.font.Font(None, 24)
    
    # Draw a background rectangle for the game over text
    game_over_bg = pygame.Surface((SCREEN_WIDTH, 200), pygame.SRCALPHA)
    game_over_bg.fill((0, 0, 0, 150))
    screen.blit(game_over_bg, (0, SCREEN_HEIGHT//2 - 150))
    
    over_text = over_font.render("Game Over", True, TEXT_COLOR)
    over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
    screen.blit(over_text, over_rect)
    
    score_text = message_font.render(f"Points: {points}   Meters: {meters}", True, TEXT_COLOR)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
    screen.blit(score_text, score_rect)
    
    message_text = message_font.render(message, True, TEXT_COLOR)
    message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
    screen.blit(message_text, message_rect)
    
    restart_btn = Button("Restart Adventure", SCREEN_WIDTH // 2 - 100, 
                           SCREEN_HEIGHT // 2 + 70, 200, 50)
    
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_btn.rect.collidepoint(event.pos):
                    waiting = False
                    return
        mouse_pos = pygame.mouse.get_pos()
        restart_btn.hover = restart_btn.rect.collidepoint(mouse_pos)
        restart_btn.draw(screen)
        pygame.display.update()

def game_loop():
    global PLAYER_SPEED
    clock = pygame.time.Clock()
    platforms = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    points = 0
    meters = 0
    game_started = False
    scroll_speed = 2  # constant scroll speed once game starts

    # Create initial platforms closer to the bottom
    start_y = SCREEN_HEIGHT - 50
    for _ in range(INITIAL_PLATFORMS):
        x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
        gap = random.randint(MIN_GAP, MAX_GAP)
        current_y = start_y - gap
        platforms.add(Platform(x, current_y))
        start_y = current_y
    
    # Spawn player on the first (lowest) platform
    first_platform = list(platforms)[0]
    player = Player(first_platform.rect.centerx, 
                    first_platform.rect.top - player_img.get_height() // 2)
    player.rect.bottom = first_platform.rect.top

    # Prepare a font for in-game score display
    try:
        score_font = pygame.font.Font("Press_Start_2P.ttf", 24)
    except:
        score_font = pygame.font.Font(None, 24)
    
    while True:
        current_time = pygame.time.get_ticks()
        
        # Spawn power-ups if points threshold reached
        if points >= SCORE_THRESHOLD:
            if current_time - POWER_UP_SPAWN_RATE > 0:  # simple check
                if len(power_ups) < 3:
                    x = random.randint(0, SCREEN_WIDTH)
                    y = -50
                    power_up_type = random.choice(POWER_UP_TYPES)
                    power_ups.add(PowerUp(x, y, power_up_type))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == USEREVENT + 1:  # Reset speed after power-up duration
                PLAYER_SPEED = 5
        
        player.update()
        
        # Set game_started flag once the player jumps for the first time.
        if not game_started and not player.on_ground and player.vel_y < 0:
            game_started = True

        # If game has started, apply constant scrolling.
        if game_started:
            player.rect.y += scroll_speed
            for plat in platforms:
                plat.rect.y += scroll_speed

        # Update moving platforms
        for plat in platforms:
            if isinstance(plat, MovingPlatform):
                plat.update()
        
        # Check collisions with power-ups
        for power_up in pygame.sprite.spritecollide(player, power_ups, True):
            power_up.activate(player)
        
        # Check collision with platforms (only if falling)
        hits = pygame.sprite.spritecollide(player, platforms, False)
        if hits and player.vel_y >= 0:
            platform = min(hits, key=lambda p: abs(player.rect.bottom - p.rect.top))
            if player.rect.bottom > platform.rect.top:
                player.rect.bottom = platform.rect.top
                player.vel_y = 0
                player.on_ground = True
                if player.last_landed_platform != platform:
                    points += 10
                    meters += 15
                    player.last_landed_platform = platform
        
        # Remove platforms that have scrolled off the bottom
        for plat in list(platforms):
            if plat.rect.top > SCREEN_HEIGHT:
                platforms.remove(plat)
        
        # Generate new platforms at the top if needed:
        if platforms:
            highest_y = min(plat.rect.y for plat in platforms)
            while highest_y > -50:
                gap = random.randint(MIN_GAP, MAX_GAP)
                new_y = highest_y - gap
                new_x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
                chance = 0.0
                if points >= 500:
                    chance = 0.3 if points < 1000 else 0.5
                if random.random() < chance:
                    new_platform = MovingPlatform(new_x, new_y)
                else:
                    new_platform = Platform(new_x, new_y)
                platforms.add(new_platform)
                highest_y = new_y
        
        # End game if player falls off the bottom of the screen
        if player.rect.top > SCREEN_HEIGHT:
            break
        
        # Draw background and sprites
        screen.blit(game_bg, (0, 0))
        platforms.draw(screen)
        power_ups.draw(screen)
        screen.blit(player.image, player.rect)
        
        # Render in-game score with a background panel
        score_panel = pygame.Surface((150, 60), pygame.SRCALPHA)
        score_panel.fill(SCORE_BG_COLOR)
        screen.blit(score_panel, (5, 5))
        score_surf = score_font.render(f"Points: {points}", True, (255, 255, 255))
        meters_surf = score_font.render(f"Meters: {meters}", True, (255, 255, 255))
        screen.blit(score_surf, (10, 10))
        screen.blit(meters_surf, (10, 35))
        
        pygame.display.update()
        clock.tick(FPS)
    
    return points, meters

def main():
    while True:
        choice = main_menu()
        if choice == "start":
            final_points, final_meters = game_loop()
            game_over_screen(final_points, final_meters)

if __name__ == "__main__":
    main()





       





















