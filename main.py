import pygame
import os
import time
import random

from pygame.constants import KEYDOWN, K_ESCAPE, K_SPACE, MOUSEBUTTONDOWN
from pygame import mixer

pygame.font.init()
pygame.init()

version_number = "Version: 2.5"

gamemode = ""

WIDTH, HEIGHT = 600, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python - Space Invaders")
icon = pygame.image.load("spaceship.png")
pygame.display.set_icon(icon)

# Load images
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))

# Player ship
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

# Lasers
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))

difficulty_settings = [1, 1, 1, 1]
difficulty_multiplier = [0]

kills = 0

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))
    
    def move(self, vel):
        self.y += vel
    
    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)

class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health = 100):
        self.x = x
        self.y = y
        self.health = health
        self.player_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 35, self.y - 30, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            bullet_sound = mixer.Sound("laser.wav")
            pygame.mixer.Sound.set_volume(bullet_sound, 0.1)
            bullet_sound.play()

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health = 100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        global kills
                        kills += 1
                        if self.lasers.count(laser) > 0:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window): 
        pygame.draw.rect(window, (255,0,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0,255,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))

class Enemy(Ship):
    COLOR_MAP = {
                "red": (RED_SPACE_SHIP, RED_LASER),
                "green": (GREEN_SPACE_SHIP, GREEN_LASER),
                "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
                }

    def __init__(self, x, y, color, health = 100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def move(self, vel):
        self.y += vel

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

def main():
    run = True
    FPS = 60
    level = 0
    lives = difficulty_settings[0]
    main_font = pygame.font.SysFont("verdana", 24)
    lost_font = pygame.font.SysFont("verdana", 60)
    subtitle_lost_font = pygame.font.SysFont("verdana", 32)
    credit_font = pygame.font.SysFont("Arial", 18)
    new_highscore_font = pygame.font.SysFont("Arial", 36)

    enemies = []
    wave_length = difficulty_settings[1]
    enemy_vel = 2  # Enemy velocity
    player_vel = 5
    laser_vel = difficulty_settings[3]

    player = Player(300, 630)

    clock = pygame.time.Clock()

    time_passed = pygame.time.get_ticks()

    lost = False
    lost_count = 0

    def redraw_window():
        WIN.blit(BG, (0,0))
        # Draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255,255,255))
        level_label = main_font.render(f"Wave: {level}", 1, (255,255,255))
        version_label = credit_font.render(version_number, 1, (128,128,128))

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        WIN.blit(version_label, (WIDTH - 100, 775))

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        if lost == True:
            scores = open("scores.txt", "r+")
            lost_label = lost_font.render("GAME OVER!", 1, (255,255,255))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))
            current_score = int((((level - 1) * 100) + (kills * 5)) * difficulty_multiplier[0])
            highscore_label = subtitle_lost_font.render("Score: " + str(current_score), 1, (255,255,255))
            WIN.blit(highscore_label, (WIDTH/2 - highscore_label.get_width()/2, 420))
            previous_highscore_label = subtitle_lost_font.render("Previous Highscore: " + str(high_score), 1, (255,255,255))
            WIN.blit(previous_highscore_label, (WIDTH/2 - previous_highscore_label.get_width()/2, 460))
            if current_score > int(high_score):
                scores.write(str(current_score))
                scores.close()
                new_highscore_label = new_highscore_font.render("New Highscore!", 1, (247,126,1))
                WIN.blit(new_highscore_label, (WIDTH/2 - new_highscore_label.get_width()/2, 240))
            
            scores.close()

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            wave_length += 2
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -50), random.choice(["red", "blue", "green", "blue"]))
                enemies.append(enemy)
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
                
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.x - player_vel > 0:  # Move left
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() < WIDTH:  # Move right
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel > 0:  # dMove up
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < HEIGHT:  # Move down, check collisions
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()
        
        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, difficulty_settings[2] * 60) == 1:
                enemy.shoot()
            
            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_vel, enemies)

def gamemode_easy():
    difficulty_settings[0] = 5  # Lives
    difficulty_settings[1] = 3  # Wave length
    difficulty_settings[2] = 5  # Enemy laser count
    difficulty_settings[3] = 6  # Laser velocity
    difficulty_multiplier[0] = 1

def gamemode_medium():
    difficulty_settings[0] = 3
    difficulty_settings[1] = 5
    difficulty_settings[2] = 4
    difficulty_settings[3] = 9
    difficulty_multiplier[0] = 1.4

def gamemode_hard():
    difficulty_settings[0] = 1
    difficulty_settings[1] = 7
    difficulty_settings[2] = 3
    difficulty_settings[3] = 12
    difficulty_multiplier[0] = 1.8

def main_menu():
    global high_score
    high_score = 0
    title_font = pygame.font.SysFont("Assistant", 80)
    subtitle_font = pygame.font.SysFont("Assistant", 50)
    difficulty_font = pygame.font.SysFont("Verdana", 24)
    difficulty_font_title = pygame.font.SysFont("Verdana", 32)
    credit_font = pygame.font.SysFont("Arial", 18)

    run = True
    while run:
        difficulty_easy = "Easy"
        difficulty_medium = "Medium"
        difficulty_hard = "Hard"
        settings_label_text = "Controls"
        WIN.blit(BG, (0,0))
        title_label = title_font.render("SPACE INVADERS", 1, (255,255,255))
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 250))
        subtitle_label = subtitle_font.render("By: Michael Tong", 1, (255,255,255))
        WIN.blit(subtitle_label, (WIDTH/2 - subtitle_label.get_width()/2, 320))
        select_difficulty_label = difficulty_font_title.render("Select difficulty:", 1, (255,255,255))
        WIN.blit(select_difficulty_label, (WIDTH/2 - select_difficulty_label.get_width()/2, 650))
        version_label = credit_font.render(version_number, 1, (128,128,128))
        WIN.blit(version_label, (WIDTH - 100, 775))

        menu_highscore_font = pygame.font.SysFont("Verdana", 18)

        scores = open("scores.txt", "r")
        high_score = int(scores.readlines()[0])
        scores.close()

        menu_previous_highscore_label = menu_highscore_font.render("Previous Highscore: " + str(high_score), 1, (255,255,255))
        WIN.blit(menu_previous_highscore_label, (WIDTH/2 - menu_previous_highscore_label.get_width()/2, 200))

        button1 = pygame.Rect(30, HEIGHT - 80, 160, 50)
        button2 = pygame.Rect(220, HEIGHT - 80, 160, 50)
        button3 = pygame.Rect(410, HEIGHT - 80, 160, 50)
        button_settings = pygame.Rect((30, 30, 160, 50))

        pygame.draw.rect(WIN, (128,128,128), button1)
        pygame.draw.rect(WIN, (128,128,128), button2)
        pygame.draw.rect(WIN, (128,128,128), button3)
        pygame.draw.rect(WIN, (128,128,128), button_settings)

        difficulty_label1 = difficulty_font.render(difficulty_easy, 1, (0,0,0))
        WIN.blit(difficulty_label1, (50, HEIGHT - 70))
        difficulty_label2 = difficulty_font.render(difficulty_medium, 1, (0,0,0))
        WIN.blit(difficulty_label2, (240, HEIGHT - 70))
        difficulty_label3 = difficulty_font.render(difficulty_hard, 1, (0,0,0))
        WIN.blit(difficulty_label3, (430, HEIGHT - 70))
        settings_label = difficulty_font.render(settings_label_text, 1, (0,0,0))
        WIN.blit(settings_label, (50, 40))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if button1.collidepoint(mouse_pos):
                    gamemode_easy()
                    main()
                if button2.collidepoint(mouse_pos):
                    gamemode_medium()
                    main()
                if button3.collidepoint(mouse_pos):
                    gamemode_hard()
                    main()
                if button_settings.collidepoint(mouse_pos):
                    print("WASD to move, spacebar to shoot, don't die, have fun!")
    pygame.quit()

main_menu()