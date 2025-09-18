# alien_game.py
import pygame
import random
import sys

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60

PLAYER_SPEED = 6
BULLET_SPEED = -10
ALIEN_ROWS = 4
ALIEN_COLS = 8
ALIEN_X_GAP = 70
ALIEN_Y_GAP = 50
ALIEN_START_Y = 60
ALIEN_SPEED_X = 1.0
ALIEN_DROP = 20

FONT_NAME = None  # default font

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Alien Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(FONT_NAME, 24)

# --- Helper functions ---
def draw_text(surf, text, size, x, y, center=True):
    f = pygame.font.Font(FONT_NAME, size)
    txt = f.render(text, True, (255, 255, 255))
    rect = txt.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(txt, rect)

# --- Game objects ---
class Player:
    def __init__(self):
        self.w, self.h = 60, 16
        self.rect = pygame.Rect((WIDTH//2 - self.w//2, HEIGHT - 60, self.w, self.h))
        self.speed = PLAYER_SPEED
        self.cooldown = 0

    def move(self, dx):
        self.rect.x += dx * self.speed
        self.rect.x = max(0, min(WIDTH - self.w, self.rect.x))

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, surf):
        # draw a simple ship (triangle + body)
        body_rect = pygame.Rect(self.rect.x, self.rect.y, self.w, self.h)
        pygame.draw.rect(surf, (0, 200, 255), body_rect)
        # triangle tip
        tip = [(self.rect.centerx, self.rect.y - 12),
               (self.rect.centerx - 12, self.rect.y + 4),
               (self.rect.centerx + 12, self.rect.y + 4)]
        pygame.draw.polygon(surf, (0, 200, 255), tip)

class Bullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 3, y, 6, 12)
        self.speed = BULLET_SPEED

    def update(self):
        self.rect.y += self.speed

    def draw(self, surf):
        pygame.draw.rect(surf, (255, 240, 60), self.rect)

class Alien:
    def __init__(self, x, y, row, col):
        self.w, self.h = 44, 28
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.row = row
        self.col = col
        self.alive = True

    def draw(self, surf):
        # simple alien: rectangle + eyes
        pygame.draw.rect(surf, (200, 50, 120), self.rect, border_radius=6)
        eye_r = 3
        pygame.draw.circle(surf, (255,255,255), (self.rect.x+12, self.rect.y+10), eye_r)
        pygame.draw.circle(surf, (255,255,255), (self.rect.x+32, self.rect.y+10), eye_r)

# --- Game logic helpers ---
def create_aliens(rows=ALIEN_ROWS, cols=ALIEN_COLS):
    aliens = []
    total_width = (cols-1)*ALIEN_X_GAP
    start_x = (WIDTH - total_width) // 2 - 22  # center them
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * ALIEN_X_GAP
            y = ALIEN_START_Y + r * ALIEN_Y_GAP
            aliens.append(Alien(x, y, r, c))
    return aliens

def aliens_bounds(aliens):
    xs = [a.rect.left for a in aliens if a.alive]
    xs2 = [a.rect.right for a in aliens if a.alive]
    if not xs:
        return None
    return min(xs), max(xs2)

# --- Main game function ---
def main():
    player = Player()
    bullets = []
    aliens = create_aliens()
    alien_dir = 1  # 1 right, -1 left
    alien_speed = ALIEN_SPEED_X
    score = 0
    lives = 3
    game_over = False
    level = 1
    shoot_cooldown = 10

    while True:
        dt = clock.tick(FPS)
        screen.fill((12, 12, 28))

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # restart
                    player = Player()
                    bullets = []
                    aliens = create_aliens()
                    alien_dir = 1
                    alien_speed = ALIEN_SPEED_X
                    score = 0
                    lives = 3
                    game_over = False
                    level = 1

        keys = pygame.key.get_pressed()
        if not game_over:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player.move(-1)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player.move(1)
            if keys[pygame.K_SPACE] and player.cooldown <= 0:
                # shoot
                bullets.append(Bullet(player.rect.centerx, player.rect.y - 10))
                player.cooldown = shoot_cooldown

        player.update()

        # --- Update bullets ---
        for b in bullets[:]:
            b.update()
            if b.rect.bottom < 0:
                bullets.remove(b)

        # --- Update aliens movement ---
        alive_aliens = [a for a in aliens if a.alive]
        if alive_aliens:
            bounds = aliens_bounds(alive_aliens)
            if bounds:
                leftmost, rightmost = bounds
                # if about to hit edges, reverse and drop
                if rightmost + alien_dir * alien_speed * FPS * 0.02 >= WIDTH - 10 or leftmost + alien_dir * alien_speed * FPS * 0.02 <= 10:
                    alien_dir *= -1
                    for a in alive_aliens:
                        a.rect.y += ALIEN_DROP
                        # if any alien too low -> lose life or game over
                        if a.rect.bottom >= player.rect.top:
                            lives = 0
                            game_over = True
                else:
                    for a in alive_aliens:
                        a.rect.x += alien_dir * alien_speed

        # --- Bullet-alien collisions ---
        for b in bullets[:]:
            for a in aliens:
                if a.alive and b.rect.colliderect(a.rect):
                    a.alive = False
                    try:
                        bullets.remove(b)
                    except ValueError:
                        pass
                    score += 10
                    break

        # --- Alien-player collision or aliens reaching bottom ---
        for a in alive_aliens:
            if a.rect.colliderect(player.rect):
                a.alive = False
                lives -= 1
                if lives <= 0:
                    game_over = True

        # --- If all aliens dead: new wave ---
        if all(not a.alive for a in aliens):
            level += 1
            alien_speed += 0.4
            aliens = create_aliens()
            # small power-up: restore one life up to 5
            if lives < 5:
                lives += 1

        # --- Draw everything ---
        player.draw(screen)
        for b in bullets:
            b.draw(screen)
        for a in aliens:
            if a.alive:
                a.draw(screen)

        # HUD
        draw_text(screen, f"Score: {score}", 22, 10, 10, center=False)
        draw_text(screen, f"Lives: {lives}", 22, WIDTH - 120, 10, center=False)
        draw_text(screen, f"Level: {level}", 22, WIDTH//2, 10, center=True)

        # Game over
        if lives <= 0:
            game_over = True

        if game_over:
            draw_text(screen, "GAME OVER", 64, WIDTH//2, HEIGHT//2 - 40)
            draw_text(screen, f"Final Score: {score}", 28, WIDTH//2, HEIGHT//2 + 20)
            draw_text(screen, "Press R to restart or close window to quit", 20, WIDTH//2, HEIGHT//2 + 60)

        pygame.display.flip()

if __name__ == "__main__":
    main()
