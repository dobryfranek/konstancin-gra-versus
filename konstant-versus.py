import threading
import ctypes
import random
import pygame
import sys
import os

def path(rel) -> str:
    if hasattr(sys, "_MEIPASS"):
        based = sys._MEIPASS
    else:
        based = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(based, rel)

pygame.init()

WIDTH, HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
FONT = pygame.font.SysFont("Consolas", int(WIDTH // 32))
scr = pygame.display.set_mode((WIDTH, HEIGHT), vsync=1, flags=pygame.FULLSCREEN)
pygame.display.set_caption("Konstancin Gra v1.3")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

PLAYER_WIDTH = WIDTH // 18
PLAYER_HEIGHT = PLAYER_WIDTH * 0.9

MATEUSZ_IMG = pygame.image.load(path("player.png"))
MATEUSZ_IMG = pygame.transform.scale(MATEUSZ_IMG, (PLAYER_WIDTH, PLAYER_HEIGHT))

ENEMY_WIDTH = WIDTH // 30
ENEMY_HEIGHT = ENEMY_WIDTH * 0.9
ENEMY_IMG = pygame.image.load(path("enemy.png")).convert_alpha()

clock = pygame.time.Clock()

class Player():
    def __init__(self, img: pygame.Surface):
        self.accel = 1
        self.x_vel = 0
        self.img = img
        self.rect = img.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT
        self.last_moved = 0
    
    def draw(self):
        self.img.set_alpha(active_color[0] / 255 * 150 + 105)
        scr.blit(self.img, self.rect.topleft)
    
    def death(self, title="ALERT", text="MATEUSZ NIE ŻYJE"):
        if hasattr(ctypes, "windll"):
            def m(title, text, icon):
                pygame.time.wait(400)
                ctypes.windll.user32.MessageBoxW(0, text, title, icon | 0x1)
            threading.Thread(target=m, args=(title, text, 0x10)).start()
        else:
            def m(title, text, icon):
                pygame.time.wait(400)
                os.system(f'zenity {icon} --title="{title}" --text="{text}"')
            threading.Thread(target=m, args=(title, text, "--error")).start()

class Enemy():
    def __init__(self, img: pygame.Surface):
        this_size = (ENEMY_WIDTH * random.uniform(0.9, 1.6), ENEMY_HEIGHT * random.uniform(0.9, 2))
        self.img = pygame.transform.scale(img, this_size)
        self.rect = self.img.get_rect()
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        self.accel = 9.81 / 32
        self.accel *= ((this_size[0] * this_size[1]) / 8192) ** 0.5
        # self.accel += random.uniform(-1/16, 1/8)
        self.velocity_y = 1
        self.is_killer = False
    
    def update(self):
        self.rect.y += self.velocity_y
        self.velocity_y += self.accel
        if self.rect.top > HEIGHT:
            self.rect.y = -self.rect.height
            self.rect.x = random.randint(0, WIDTH - self.rect.width)
            self.velocity_y = 0

    def draw(self):
        if not self.is_killer:
            self.img.set_alpha(active_color[0] / 255 * 150 + 105)
        else:
            self.img.set_alpha(255)
        scr.blit(self.img, self.rect.topleft)

    def is_collision(self, player):
        # if player is None:
        #     return False

        # if self.rect.y > player.rect.centery:
        #     return False
        
        # if not self.rect.colliderect(player.rect):
        #     return False

        if (player is None) or (self.rect.centery > player.rect.centery) or (not self.rect.colliderect(player.rect)):
            return False
    
        for x in range(self.rect.left, self.rect.right):
            for y in range(self.rect.top, self.rect.bottom):
                if player.rect.collidepoint(x, y):
                    if self.img.get_at((x - self.rect.left, y - self.rect.top))[3] > 0:
                        self.is_killer = True
                        return True
        return False

class TemporaryEnemy(Enemy):
    def __init__(self, img):
        super().__init__(img)
        self.rect.centerx = gierek.rect.centerx + random.randint(-PLAYER_WIDTH,PLAYER_WIDTH)
    
    def update(self):
        self.rect.y += self.velocity_y
        self.velocity_y += self.accel
        if self.rect.top > HEIGHT:
            self.rect.y = -self.rect.height
            self.rect.x = random.randint(0, WIDTH - self.rect.width)
            self.velocity_y = 0
            enemies.remove(self)


score = 0

def draw_score():
    surf = FONT.render(str(score), False, tuple(255 - i for i in active_color))
    scr.blit(surf, (WIDTH - surf.get_width(), 0))

gierek = Player(MATEUSZ_IMG)
enemies = list()
enemies = [Enemy(ENEMY_IMG) for _ in range(1)]

def get_next_color(current: tuple, is_day: bool) -> tuple[tuple, bool]:
    animation_should_run = 1
    if is_day:
        next_color = tuple(i + 1 for i in current)
        if next_color[0] >= 255:
            next_color = (255, 255, 255)
            animation_should_run = 0

    else:
        next_color = tuple(i - 1 for i in current)
        if next_color[0] <= 0:
            next_color = (0, 0, 0)
            animation_should_run = 0

    return (next_color, animation_should_run)

game_time = 1
friction = 0.97
is_day = 1
active_color = WHITE if is_day else BLACK
animation_running = 0

running = 1
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = 0
    
    k_pressed = pygame.key.get_pressed()

    if k_pressed[pygame.K_d]:
        gierek.x_vel += gierek.accel
    if k_pressed[pygame.K_a]:
        gierek.x_vel -= gierek.accel

    if k_pressed[pygame.K_s]:
        friction = 0.8
    else:
        friction = 0.97

    if abs(gierek.x_vel) > 1:
        gierek.last_moved = game_time

    gierek.x_vel *= friction # tarcie
    gierek.rect.x += gierek.x_vel
    

    if game_time - gierek.last_moved > 100:
        enemies.append(TemporaryEnemy(ENEMY_IMG))
        gierek.last_moved = game_time

    if game_time % 400 == 0:
        for _ in range(2): enemies.append(Enemy(ENEMY_IMG))
    
    if game_time % 750 == 0:
        is_day = not is_day
        animation_running = 1


    if gierek.rect.left < 0:
        nowy_gierk = Player(MATEUSZ_IMG)
        nowy_gierk.rect.x = gierek.rect.x + WIDTH
    elif gierek.rect.right > WIDTH:
        nowy_gierk = Player(MATEUSZ_IMG)
        nowy_gierk.rect.x = gierek.rect.x - WIDTH
    else:
        nowy_gierk = None
    

    if gierek.rect.left < -gierek.rect.w:
        gierek.rect.x += WIDTH
        nowy_gierk = None
    
    elif gierek.rect.right > WIDTH + gierek.rect.w:
        gierek.rect.x -= WIDTH

    if nowy_gierk is not None:
        nowy_gierk.draw()


    for enemy in enemies:
        enemy.update()
        if enemy.is_collision(gierek) or enemy.is_collision(nowy_gierk):
            gierek.death(title="WYNIK: " + str(score))
            running = 0

    gierek.draw()

    for enemy in enemies:
        enemy.draw()

    draw_score()

    if animation_running:
        active_color, animation_running = get_next_color(active_color, is_day)

    pygame.display.flip()
    scr.fill(active_color)
    clock.tick(75)
    game_time += 1
    score = game_time // 50 * 50

    if running == 0:
        pygame.time.wait(350) #show impact
    

pygame.quit()