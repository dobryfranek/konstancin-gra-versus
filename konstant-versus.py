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
pygame.display.set_caption("Konstancin Gra Versus v1.0")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

BASE_FRICTION = 0.97
SLOWED_FRICTION = 0.8

PLAYER_WIDTH = WIDTH // 18
PLAYER_HEIGHT = PLAYER_WIDTH * 0.9

MATEUSZ_IMG = pygame.image.load(path("player1.png"))
MATEUSZ_IMG = pygame.transform.scale(MATEUSZ_IMG, (PLAYER_WIDTH, PLAYER_HEIGHT))

PAWEL_IMG = pygame.image.load(path("player2.png"))
PAWEL_IMG = pygame.transform.scale(PAWEL_IMG, (PLAYER_WIDTH, PLAYER_HEIGHT))

ENEMY_WIDTH = WIDTH // 30
ENEMY_HEIGHT = ENEMY_WIDTH * 0.9
ENEMY_IMG = pygame.image.load(path("enemy.png")).convert_alpha()

clock = pygame.time.Clock()

class Player():
    def __init__(self, img: pygame.Surface, name: str):
        self.friction = BASE_FRICTION
        self.name = name
        self.accel = 1
        self.x_vel = 0
        self.img = img
        self.rect = img.get_rect()
        match self.name:
            case "mateusz":
                self.rect.centerx = WIDTH // 4
            case "paweł":
                self.rect.centerx = WIDTH // 4 * 3
        
        self.rect.bottom = HEIGHT
        self.last_moved = 0
    
    def draw(self):
        if self.name != "paweł":
            self.img.set_alpha(active_color[0] / 255 * 120 + 135)
        else:
            self.img.set_alpha(active_color[0] / 255 * 90 + 165) #zdjęcie player2.png i tak jest ciemniejsze
        scr.blit(self.img, self.rect.topleft)
    
    def death(self, title="ALERT", tie: bool = False):
        if not tie:
            text = self.name.upper() + " NIE ŻYJE"
        else:
            text = "WSZYSCY ZMARLI"

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
    def __init__(self, img, gier: Player):
        super().__init__(img)
        self.rect.centerx = gier.rect.centerx + random.randint(-PLAYER_WIDTH,PLAYER_WIDTH)
    
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

gierek1 = Player(MATEUSZ_IMG, "mateusz")
gierek2 = Player(PAWEL_IMG, "paweł")

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
is_day = 1
active_color = WHITE if is_day else BLACK
animation_running = 0

running = 1
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = 0
    
    k_pressed = pygame.key.get_pressed()

    #MATEUSZ
    if k_pressed[pygame.K_d]:
        gierek1.x_vel += gierek1.accel
    if k_pressed[pygame.K_a]:
        gierek1.x_vel -= gierek1.accel

    if k_pressed[pygame.K_s]:
        gierek1.friction = SLOWED_FRICTION
    else:
        gierek1.friction = BASE_FRICTION

    gierek1.x_vel *= gierek1.friction # tarcie

    if abs(gierek1.x_vel) < 0.1:
        gierek1.x_vel = 0

    gierek1.rect.x += gierek1.x_vel

    if abs(gierek1.x_vel) > 1:
        gierek1.last_moved = game_time

    if game_time - gierek1.last_moved > 100:
        enemies.append(TemporaryEnemy(ENEMY_IMG, gierek1))
        gierek1.last_moved = game_time

    if gierek1.rect.left < 0:
        nowy_gierk1 = Player(MATEUSZ_IMG, "mateusz")
        nowy_gierk1.rect.x = gierek1.rect.x + WIDTH
    elif gierek1.rect.right > WIDTH:
        nowy_gierk1 = Player(MATEUSZ_IMG, "mateusz")
        nowy_gierk1.rect.x = gierek1.rect.x - WIDTH
    else:
        nowy_gierk1 = None

    if gierek1.rect.left < -gierek1.rect.w:
        gierek1.rect.x += WIDTH
        nowy_gierk1 = None
    
    elif gierek1.rect.right > WIDTH + gierek1.rect.w:
        gierek1.rect.x -= WIDTH
        nowy_gierk1 = None


    #PAWEŁ
    if k_pressed[pygame.K_RIGHT]:
        gierek2.x_vel += gierek2.accel
    if k_pressed[pygame.K_LEFT]:
        gierek2.x_vel -= gierek2.accel

    if k_pressed[pygame.K_DOWN]:
        gierek2.friction = SLOWED_FRICTION
    else:
        gierek2.friction = BASE_FRICTION

    gierek2.x_vel *= gierek2.friction # tarcie

    if abs(gierek2.x_vel) < 0.1:
        gierek2.x_vel = 0

    gierek2.rect.x += gierek2.x_vel


    if abs(gierek2.x_vel) > 1:
        gierek2.last_moved = game_time

    if game_time - gierek2.last_moved > 100:
        enemies.append(TemporaryEnemy(ENEMY_IMG, gierek2))
        gierek2.last_moved = game_time
    
    if gierek2.rect.left < 0:
        nowy_gierk2 = Player(PAWEL_IMG, "paweł")
        nowy_gierk2.rect.x = gierek2.rect.x + WIDTH
    elif gierek2.rect.right > WIDTH:
        nowy_gierk2 = Player(PAWEL_IMG, "paweł")
        nowy_gierk2.rect.x = gierek2.rect.x - WIDTH
    else:
        nowy_gierk2 = None

    if gierek2.rect.left < -gierek2.rect.w:
        gierek2.rect.x += WIDTH
        nowy_gierk2 = None
    
    elif gierek2.rect.right > WIDTH + gierek2.rect.w:
        gierek2.rect.x -= WIDTH
        nowy_gierk2 = None

    if game_time % 400 == 0:
        for _ in range(2): enemies.append(Enemy(ENEMY_IMG))
    
    if game_time % 750 == 0:
        is_day = not is_day
        animation_running = 1

    for enemy in enemies:
        enemy.update()
        if (enemy.is_collision(gierek1) or enemy.is_collision(nowy_gierk1)) and (enemy.is_collision(gierek2) or enemy.is_collision(nowy_gierk2)):
            gierek1.death(tie=True)
            running = 0

        else:
            if enemy.is_collision(gierek1) or enemy.is_collision(nowy_gierk1):
                gierek1.death()
                running = 0
            if enemy.is_collision(gierek2) or enemy.is_collision(nowy_gierk2):
                gierek2.death()
                running = 0
        
    if nowy_gierk1 is not None:
        nowy_gierk1.draw()

    if nowy_gierk2 is not None:
        nowy_gierk2.draw()

    gierek2.draw()
    gierek1.draw()

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
