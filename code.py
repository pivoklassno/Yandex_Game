import pygame, sys, os
import random

pygame.init()
BASE_WIDTH, BASE_HEIGHT = 800, 600
display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Толстый и Тонкий")
clock = pygame.time.Clock()
window_size = display_surface.get_size()
game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
font = pygame.font.Font("freesansbold.ttf", 40)
GRAVITY = 1
UNIT_SIZE = 10


# Загрузка спрайтов
def load_sprite(path, scale=None):
    img = pygame.image.load(os.path.join("sprites", path))
    if scale: img = pygame.transform.scale(img, scale)
    return img


# Фоновое изображение
bg_tile = load_sprite("bg.jpg", (UNIT_SIZE, UNIT_SIZE))

# Основные спрайты
block_img = load_sprite("block.jpg")
platform_tile = load_sprite("platform.jpg", (UNIT_SIZE, UNIT_SIZE))
coin_img = load_sprite("coin.png")
door_img = load_sprite("door.jpg")
key_img = load_sprite("key.png")
spike_img = load_sprite("spike.png")

# Кнопки и стена
button_imgs = [
    load_sprite("button_1.jpg"),
    load_sprite("button_2.jpg")
]

wall_anim = [
    load_sprite("wall_1.jpg"),
    load_sprite("wall_2.jpg"),
    load_sprite("wall_3.jpg"),
    load_sprite("wall_4.jpg")
]


# Частицы
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-5, -1)
        self.lifetime = 30
        self.image = pygame.transform.scale(spike_img, (5, 5))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            surface.blit(self.image, (self.x, self.y))


def draw_background(surface):
    for x in range(0, BASE_WIDTH, UNIT_SIZE):
        for y in range(0, BASE_HEIGHT, UNIT_SIZE):
            surface.blit(bg_tile, (x, y))


def get_game_mouse_pos():
    mx, my = pygame.mouse.get_pos()
    inv_scale_x = BASE_WIDTH / window_size[0]
    inv_scale_y = BASE_HEIGHT / window_size[1]
    return mx * inv_scale_x, my * inv_scale_y


def get_text_rect(text, center):
    surf = font.render(text, True, (255, 255, 255))
    return surf.get_rect(center=center)


def render_text(text, center, color):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    game_surface.blit(surf, rect)
    return rect


class Player:
    def __init__(self, x, y, w, h, color, speed, jump_strength, is_fat=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.speed = speed
        self.jump_strength = jump_strength
        self.vel_y = 0
        self.on_ground = False
        self.has_key = False
        self.is_fat = is_fat
        self.direction = 1
        self.particles = []

    def update(self, platforms, blocks):
        move_x = self.speed_x if hasattr(self, 'speed_x') else 0

        # Генерация частиц при движении толстого
        if self.is_fat and self.on_ground:
            if (move_x > 0 and self.direction < 0) or (move_x < 0 and self.direction > 0):
                if random.random() < 0.5:
                    self.particles.append(Particle(
                        self.rect.centerx + random.randint(-10, 10),
                        self.rect.bottom - 5
                    ))

        if move_x != 0:
            self.direction = 1 if move_x > 0 else -1

        # Обновление частиц
        for p in self.particles[:]:
            p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)

        self.rect.x += move_x
        for plat in platforms:
            if self.rect.colliderect(plat):
                if move_x > 0:
                    self.rect.right = plat.left
                elif move_x < 0:
                    self.rect.left = plat.right
        for block in blocks:
            if self.rect.colliderect(block.rect):
                if self.is_fat:
                    block.rect.x += move_x
                else:
                    if move_x > 0:
                        self.rect.right = block.rect.left
                    elif move_x < 0:
                        self.rect.left = block.rect.right

        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        self.on_ground = False

        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vel_y > 0:
                    self.rect.bottom = plat.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = plat.bottom
                    self.vel_y = 0

        for block in blocks:
            if self.rect.colliderect(block.rect):
                if self.vel_y > 0:
                    self.rect.bottom = block.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.rect.bottom
                    self.vel_y = 0

        if self.rect.bottom >= BASE_HEIGHT and self.vel_y >= 0:
            self.rect.bottom = BASE_HEIGHT
            self.vel_y = 0
            self.on_ground = True

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > BASE_WIDTH:
            self.rect.right = BASE_WIDTH

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        for p in self.particles:
            p.draw(surface)


class BlockObj:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.vel_y = 0
        self.image = pygame.transform.scale(block_img, (w, h))

    def update(self, platforms):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.vel_y > 0:
                    self.rect.bottom = plat.top
                    self.vel_y = 0
                elif self.vel_y < 0:
                    self.rect.top = plat.bottom
                    self.vel_y = 0
        if self.rect.bottom >= BASE_HEIGHT:
            self.rect.bottom = BASE_HEIGHT
            self.vel_y = 0

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class ButtonObj:
    def __init__(self, x, y, w=60, h=20):
        self.rect = pygame.Rect(x, y, w, h)
        self.activated = False
        self.normal_h = h
        self.img = [
            pygame.transform.scale(button_imgs[0], (w, h)),
            pygame.transform.scale(button_imgs[1], (w, h // 3))
        ]

    def activate(self):
        if not self.activated:
            self.activated = True
            self.rect.height = self.normal_h // 3

    def draw(self, surface):
        img = self.img[1] if self.activated else self.img[0]
        surface.blit(img, self.rect)


class Barrier:
    def __init__(self, x, y, w=20, h=80):
        self.rect = pygame.Rect(x, y, w, h)
        self.active = True
        self.anim_frame = 0
        self.anim_timer = 0
        self.frames = [pygame.transform.scale(img, (w, h)) for img in wall_anim]

    def update(self, dt):
        if not self.active and self.anim_frame < 3:
            self.anim_timer += dt
            if self.anim_timer >= 200:
                self.anim_frame += 1
                self.anim_timer = 0

    def draw(self, surface):
        if self.active:
            surface.blit(self.frames[0], self.rect)
        else:
            if self.anim_frame < 3:
                surface.blit(self.frames[self.anim_frame], self.rect)


thin = Player(100, BASE_HEIGHT - 80, 30, 80, (0, 255, 0), 7, -15)
fat = Player(300, BASE_HEIGHT - 40, 50, 40, (255, 0, 0), 5, -12, is_fat=True)
state = "menu"
paused = False
death = False
level_completed = False
platforms = []
spikes = []
keys = []
doors = []
blocks = []
buttons = []
barriers = []
coins = []
coins_collected = 0
spawn_thin = None
spawn_fat = None
selected_tool = None
tool_list = ["Платформа", "Шипы", "Ключ", "Дверь", "Кнопка", "Блок", "Преграда", "Спавн Тонкого", "Спавн Толстого",
             "Монетка"]
sizing_menu_active = False
sizing_menu_click_pos = (0, 0)
current_platform_width_units = 1
current_platform_height_units = 1
tools_menu_active = False
level_name_input_active = False
level_name = ""
current_level_name = None


def save_level(filename):
    if not os.path.exists("levels"):
        os.makedirs("levels")
    filepath = os.path.join("levels", filename + ".txt")
    with open(filepath, "w") as file:
        for plat in platforms:
            file.write(f"{plat.x},{plat.y},{plat.width},{plat.height}\n")
        for spike in spikes:
            file.write(f"spike,{spike.x},{spike.y},{spike.width},{spike.height}\n")
        for key_rect in keys:
            file.write(f"key,{key_rect.x},{key_rect.y},{key_rect.width},{key_rect.height}\n")
        for coin in coins:
            file.write(f"coin,{coin.x},{coin.y},{coin.width},{coin.height}\n")
        for door_rect in doors:
            file.write(f"door,{door_rect.x},{door_rect.y},{door_rect.width},{door_rect.height}\n")
        for block in blocks:
            file.write(f"block,{block.rect.x},{block.rect.y},{block.rect.width},{block.rect.height}\n")
        for btn in buttons:
            file.write(
                f"button,{btn.rect.x},{btn.rect.y},{btn.rect.width},{btn.rect.height},{1 if btn.activated else 0}\n")
        for barr in barriers:
            file.write(
                f"barrier,{barr.rect.x},{barr.rect.y},{barr.rect.width},{barr.rect.height},{1 if barr.active else 0}\n")
        if spawn_thin is not None:
            file.write(f"spawn_thin,{int(spawn_thin[0])},{int(spawn_thin[1])}\n")
        if spawn_fat is not None:
            file.write(f"spawn_fat,{int(spawn_fat[0])},{int(spawn_fat[1])}\n")
    print(f"Level saved to {filepath}")


def load_level(filename):
    global spawn_thin, spawn_fat, coins_collected
    coins_collected = 0
    platforms.clear()
    spikes.clear()
    keys.clear()
    doors.clear()
    blocks.clear()
    buttons.clear()
    barriers.clear()
    spawn_thin = None
    spawn_fat = None
    filepath = os.path.join("levels", filename + ".txt")
    try:
        with open(filepath, "r") as file:
            for line in file:
                parts = line.strip().split(",")
                if parts[0] == "spike":
                    _, x, y, width, height = parts
                    spikes.append(pygame.Rect(int(x), int(y), int(width), int(height)))
                elif parts[0] == "coin":
                    _, x, y, width, height = parts
                    coins.append(pygame.Rect(int(x), int(y), int(width), int(height)))
                elif parts[0] == "key":
                    _, x, y, width, height = parts
                    keys.append(pygame.Rect(int(x), int(y), int(width), int(height)))
                elif parts[0] == "door":
                    _, x, y, width, height = parts
                    doors.append(pygame.Rect(int(x), int(y), int(width), int(height)))
                elif parts[0] == "block":
                    _, x, y, width, height = parts
                    blocks.append(BlockObj(int(x), int(y), int(width), int(height)))
                elif parts[0] == "button":
                    _, x, y, width, height, act = parts
                    btn = ButtonObj(int(x), int(y), int(width), int(height))
                    btn.activated = (act == "1")
                    buttons.append(btn)
                elif parts[0] == "barrier":
                    _, x, y, width, height, act = parts
                    barr = Barrier(int(x), int(y), int(width), int(height))
                    barr.active = (act == "1")
                    barriers.append(barr)
                elif parts[0] == "spawn_thin":
                    _, x, y = parts
                    spawn_thin = (int(x), int(y))
                elif parts[0] == "spawn_fat":
                    _, x, y = parts
                    spawn_fat = (int(x), int(y))
                else:
                    x, y, width, height = map(int, parts)
                    platforms.append(pygame.Rect(x, y, width, height))
    except FileNotFoundError:
        print(f"Level file not found: {filepath}")


while True:
    dt = clock.get_time()
    window_size = display_surface.get_size()

    if state == "menu":
        game_surface.fill((30, 30, 30))
        draw_background(game_surface)
        play_btn_rect = get_text_rect("Играть", (BASE_WIDTH // 2, 250))
        editor_btn_rect = get_text_rect("Редактор уровней", (BASE_WIDTH // 2, 320))
        exit_btn_rect = get_text_rect("Выход", (BASE_WIDTH // 2, 390))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                gx, gy = get_game_mouse_pos()
                if play_btn_rect.collidepoint((gx, gy)):
                    state = "level_select"
                elif editor_btn_rect.collidepoint((gx, gy)):
                    state = "editor"
                    platforms = []
                    spikes = []
                    keys = []
                    doors = []
                    blocks = []
                    buttons = []
                    barriers = []
                    spawn_thin = None
                    spawn_fat = None
                    selected_tool = None
                elif exit_btn_rect.collidepoint((gx, gy)):
                    pygame.quit()
                    sys.exit()

        mx, my = get_game_mouse_pos()
        play_color = (255, 255, 0) if play_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
        play_btn_rect = render_text("Играть", (BASE_WIDTH // 2, 250), play_color)
        editor_color = (255, 255, 0) if editor_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
        editor_btn_rect = render_text("Редактор уровней", (BASE_WIDTH // 2, 320), editor_color)
        exit_color = (255, 255, 0) if exit_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
        exit_btn_rect = render_text("Выход", (BASE_WIDTH // 2, 390), exit_color)

        scaled_surface = pygame.transform.scale(game_surface, window_size)
        display_surface.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    elif state == "level_select":
        coins_collected = 0
        game_surface.fill((30, 30, 30))
        draw_background(game_surface)
        level_files = [f[:-4] for f in os.listdir("levels") if f.endswith(".txt")]
        level_rects = []
        y_offset = 200

        for i, lvl in enumerate(level_files):
            lvl_rect = get_text_rect(lvl, (BASE_WIDTH // 2, y_offset + i * 50))
            level_rects.append((lvl_rect, lvl))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state = "menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                gx, gy = get_game_mouse_pos()
                for rect, lvl in level_rects:
                    if rect.collidepoint((gx, gy)):
                        current_level_name = lvl
                        load_level(lvl)
                        if spawn_thin is not None:
                            thin = Player(spawn_thin[0], spawn_thin[1] - 80, 30, 80, (0, 255, 0), 7, -15)
                        else:
                            thin = Player(100, BASE_HEIGHT - 80, 30, 80, (0, 255, 0), 7, -15)
                        if spawn_fat is not None:
                            fat = Player(spawn_fat[0], spawn_fat[1] - 40, 50, 40, (255, 0, 0), 5, -12, is_fat=True)
                        else:
                            fat = Player(300, BASE_HEIGHT - 40, 50, 40, (255, 0, 0), 5, -12, is_fat=True)
                        paused = False
                        death = False
                        level_completed = False
                        state = "game"
                        break

        render_text("Выберите уровень:", (BASE_WIDTH // 2, 150), (255, 255, 255))
        mx, my = get_game_mouse_pos()
        for rect, lvl in level_rects:
            color = (255, 255, 0) if rect.collidepoint((mx, my)) else (255, 255, 255)
            render_text(lvl, (BASE_WIDTH // 2, rect.centery), color)

        scaled_surface = pygame.transform.scale(game_surface, window_size)
        display_surface.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    elif state == "editor":
        game_surface.fill((180, 180, 180))
        draw_background(game_surface)
        save_btn_rect = get_text_rect("Сохранить", (BASE_WIDTH - 100, 30))
        tools_btn_rect = get_text_rect("Инструменты", (160, 30))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if level_name_input_active:
                    if event.key == pygame.K_RETURN:
                        save_level(level_name)
                        level_name_input_active = False
                        level_name = ""
                    elif event.key == pygame.K_ESCAPE:
                        level_name_input_active = False
                        level_name = ""
                    elif event.key == pygame.K_BACKSPACE:
                        level_name = level_name[:-1]
                    else:
                        level_name += event.unicode
                elif sizing_menu_active:
                    if event.key == pygame.K_RIGHT:
                        current_platform_width_units += 1
                    elif event.key == pygame.K_LEFT and current_platform_width_units > 1:
                        current_platform_width_units -= 1
                    elif event.key == pygame.K_UP:
                        current_platform_height_units += 1
                    elif event.key == pygame.K_DOWN and current_platform_height_units > 1:
                        current_platform_height_units -= 1
                    elif event.key == pygame.K_RETURN:
                        pw = current_platform_width_units * UNIT_SIZE
                        ph = current_platform_height_units * UNIT_SIZE
                        plat_rect = pygame.Rect(sizing_menu_click_pos[0], sizing_menu_click_pos[1] - ph, pw, ph)
                        platforms.append(plat_rect)
                        sizing_menu_active = False
                    elif event.key == pygame.K_ESCAPE:
                        sizing_menu_active = False
                else:
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
            if event.type == pygame.MOUSEBUTTONDOWN:
                gx, gy = get_game_mouse_pos()
                if event.button == 1:
                    if save_btn_rect.collidepoint((gx, gy)):
                        level_name_input_active = True
                    elif tools_btn_rect.collidepoint((gx, gy)):
                        tools_menu_active = not tools_menu_active
                    elif tools_menu_active:
                        plat_opt = render_text("Платформа", (160, 70), (255, 255, 255))
                        spike_opt = render_text("Шипы", (160, 100), (255, 255, 255))
                        key_opt = render_text("Ключ", (160, 130), (255, 255, 255))
                        door_opt = render_text("Дверь", (160, 160), (255, 255, 255))
                        button_opt = render_text("Кнопка", (160, 190), (255, 255, 255))
                        block_opt = render_text("Блок", (160, 220), (255, 255, 255))
                        barrier_opt = render_text("Преграда", (160, 250), (255, 255, 255))
                        spawn_thin_opt = render_text("Спавн Тонкого", (160, 280), (255, 255, 255))
                        spawn_fat_opt = render_text("Спавн Толстого", (160, 310), (255, 255, 255))
                        coin_opt = render_text("Монетка", (160, 340), (255, 255, 255))
                        if plat_opt.collidepoint((gx, gy)):
                            selected_tool = "Платформа"
                            tools_menu_active = False
                        elif spike_opt.collidepoint((gx, gy)):
                            selected_tool = "Шипы"
                            tools_menu_active = False
                        elif coin_opt.collidepoint((gx, gy)):
                            selected_tool = "Монетка"
                            tools_menu_active = False
                        elif key_opt.collidepoint((gx, gy)):
                            selected_tool = "Ключ"
                            tools_menu_active = False
                        elif door_opt.collidepoint((gx, gy)):
                            selected_tool = "Дверь"
                            tools_menu_active = False
                        elif button_opt.collidepoint((gx, gy)):
                            selected_tool = "Кнопка"
                            tools_menu_active = False
                        elif block_opt.collidepoint((gx, gy)):
                            selected_tool = "Блок"
                            tools_menu_active = False
                        elif barrier_opt.collidepoint((gx, gy)):
                            selected_tool = "Преграда"
                            tools_menu_active = False
                        elif spawn_thin_opt.collidepoint((gx, gy)):
                            selected_tool = "Спавн Тонкого"
                            tools_menu_active = False
                        elif spawn_fat_opt.collidepoint((gx, gy)):
                            selected_tool = "Спавн Толстого"
                            tools_menu_active = False
                    else:
                        if selected_tool == "Платформа":
                            tool_btn_rect = get_text_rect("Платформа", (60, 20))
                            if tool_btn_rect.collidepoint((gx, gy)):
                                selected_tool = "Платформа"
                            elif not sizing_menu_active and not level_name_input_active:
                                sizing_menu_active = True
                                sizing_menu_click_pos = (gx, gy)
                                current_platform_width_units = 1
                                current_platform_height_units = 1
                        elif selected_tool == "Шипы":
                            spike_size = fat.rect.height // 2
                            spike_rect = pygame.Rect(gx, gy - spike_size, spike_size, spike_size)
                            spikes.append(spike_rect)
                        elif selected_tool == "Монетка":
                            coin_size = 20
                            coin_rect = pygame.Rect(gx - coin_size // 2, gy - coin_size // 2, coin_size, coin_size)
                            coins.append(coin_rect)
                        elif selected_tool == "Ключ":
                            key_rect = pygame.Rect(gx, gy, 20, 20)
                            keys.append(key_rect)
                        elif selected_tool == "Дверь":
                            door_rect = pygame.Rect(gx, gy, 40, 80)
                            doors.append(door_rect)
                        elif selected_tool == "Кнопка":
                            buttons.append(ButtonObj(gx, gy, 60, 20))
                        elif selected_tool == "Блок":
                            blocks.append(BlockObj(gx, gy - 40, 40, 40))
                        elif selected_tool == "Преграда":
                            barriers.append(Barrier(gx, gy, 20, 80))
                        elif selected_tool == "Спавн Тонкого":
                            spawn_thin = (int(gx), int(gy))
                        elif selected_tool == "Спавн Толстого":
                            spawn_fat = (int(gx), int(gy))
                elif event.button == 3:
                    removed = False
                    for plat in platforms[:]:
                        if plat.collidepoint((gx, gy)):
                            platforms.remove(plat)
                            removed = True
                            break
                    if not removed:
                        for spike in spikes[:]:
                            if spike.collidepoint((gx, gy)):
                                spikes.remove(spike)
                                removed = True
                                break
                    if not removed:
                        for coin in coins[:]:
                            if coin.collidepoint((gx, gy)):
                                coins.remove(coin)
                                removed = True
                                break
                    if not removed:
                        for block in blocks[:]:
                            if block.rect.collidepoint((gx, gy)):
                                blocks.remove(block)
                                removed = True
                                break
                    if not removed:
                        for btn in buttons[:]:
                            if btn.rect.collidepoint((gx, gy)):
                                buttons.remove(btn)
                                removed = True
                                break
                    if not removed:
                        for barr in barriers[:]:
                            if barr.rect.collidepoint((gx, gy)):
                                barriers.remove(barr)
                                removed = True
                                break

        mx, my = get_game_mouse_pos()
        save_color = (255, 255, 0) if save_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
        save_btn_rect = render_text("Сохранить", (BASE_WIDTH - 100, 30), save_color)
        tools_color = (255, 255, 0) if tools_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
        tools_btn_rect = render_text("Инструменты", (160, 30), tools_color)

        if tools_menu_active:
            render_text("Платформа", (160, 70), (255, 255, 255))
            render_text("Шипы", (160, 100), (255, 255, 255))
            render_text("Ключ", (160, 130), (255, 255, 255))
            render_text("Дверь", (160, 160), (255, 255, 255))
            render_text("Кнопка", (160, 190), (255, 255, 255))
            render_text("Блок", (160, 220), (255, 255, 255))
            render_text("Преграда", (160, 250), (255, 255, 255))
            render_text("Спавн Тонкого", (160, 280), (255, 255, 255))
            render_text("Спавн Толстого", (160, 310), (255, 255, 255))
            render_text("Монетка", (160, 340), (255, 255, 255))

        if selected_tool:
            render_text(selected_tool, (BASE_WIDTH // 2, 30), (255, 255, 255))

        for plat in platforms:
            tile = platform_tile
            for x in range(0, plat.width, UNIT_SIZE):
                for y in range(0, plat.height, UNIT_SIZE):
                    game_surface.blit(tile, (plat.x + x, plat.y + y))

        for spike in spikes:
            img = pygame.transform.scale(spike_img, (spike.width, spike.height))
            game_surface.blit(img, spike)

        for key_rect in keys:
            img = pygame.transform.scale(key_img, (key_rect.width, key_rect.height))
            game_surface.blit(img, key_rect)

        for door_rect in doors:
            img = pygame.transform.scale(door_img, (door_rect.width, door_rect.height))
            game_surface.blit(img, door_rect)

        for coin in coins:
            img = pygame.transform.scale(coin_img, (coin.width, coin.height))
            game_surface.blit(img, coin)

        for block in blocks:
            block.draw(game_surface)

        for btn in buttons:
            btn.draw(game_surface)

        for barr in barriers:
            barr.update(dt)
            barr.draw(game_surface)

        if spawn_thin is not None:
            pygame.draw.circle(game_surface, (0, 255, 0), spawn_thin, 5)
        if spawn_fat is not None:
            pygame.draw.circle(game_surface, (255, 0, 0), spawn_fat, 5)

        if sizing_menu_active:
            menu_rect = pygame.Rect((BASE_WIDTH - 300) // 2, (BASE_HEIGHT - 150) // 2, 300, 150)
            pygame.draw.rect(game_surface, (0, 0, 0), menu_rect)
            title_surf = font.render("Настройка платформы", True, (255, 255, 255))
            game_surface.blit(title_surf, title_surf.get_rect(center=(menu_rect.centerx, menu_rect.y + 20)))
            size_surf = font.render(f"Ширина: {current_platform_width_units}  Высота: {current_platform_height_units}",
                                    True, (255, 255, 255))
            game_surface.blit(size_surf, size_surf.get_rect(center=(menu_rect.centerx, menu_rect.y + 60)))
            instr_surf = font.render("←/→: ширина, ↑/↓: высота", True, (255, 255, 255))
            game_surface.blit(instr_surf, instr_surf.get_rect(center=(menu_rect.centerx, menu_rect.y + 100)))
            confirm_surf = font.render("Enter: подтвердить, Esc: отмена", True, (255, 255, 255))
            game_surface.blit(confirm_surf, confirm_surf.get_rect(center=(menu_rect.centerx, menu_rect.y + 130)))

        if level_name_input_active:
            input_rect = pygame.Rect((BASE_WIDTH - 300) // 2, (BASE_HEIGHT - 100) // 2, 300, 50)
            pygame.draw.rect(game_surface, (0, 0, 0), input_rect)
            text_surf = font.render(level_name, True, (255, 255, 255))
            game_surface.blit(text_surf, text_surf.get_rect(center=input_rect.center))

        scaled_surface = pygame.transform.scale(game_surface, window_size)
        display_surface.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    elif state == "game":
        game_surface.fill((200, 200, 200))
        draw_background(game_surface)
        pause_btn_rect = get_text_rect("Пауза", (BASE_WIDTH - 60, 30))
        restart_btn_rect = get_text_rect("Заново", (BASE_WIDTH // 2, BASE_HEIGHT // 2 - 20))
        continue_btn_rect = get_text_rect("Продолжить", (BASE_WIDTH // 2, BASE_HEIGHT // 2 - 20))
        menu_btn_rect = get_text_rect("Выйти в меню", (BASE_WIDTH // 2, BASE_HEIGHT // 2 + 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                gx, gy = get_game_mouse_pos()
                if not paused:
                    if pause_btn_rect.collidepoint((gx, gy)):
                        paused = True
                else:
                    if death or level_completed:
                        if restart_btn_rect.collidepoint((gx, gy)):
                            if current_level_name is not None:
                                load_level(current_level_name)
                            if spawn_thin is not None:
                                thin = Player(spawn_thin[0], spawn_thin[1] - 80, 30, 80, (0, 255, 0), 7, -15)
                            else:
                                thin = Player(100, BASE_HEIGHT - 80, 30, 80, (0, 255, 0), 7, -15)
                            if spawn_fat is not None:
                                fat = Player(spawn_fat[0], spawn_fat[1] - 40, 50, 40, (255, 0, 0), 5, -12, is_fat=True)
                            else:
                                fat = Player(300, BASE_HEIGHT - 40, 50, 40, (255, 0, 0), 5, -12, is_fat=True)
                            paused = False
                            death = False
                            level_completed = False
                            coins_collected = 0
                        elif menu_btn_rect.collidepoint((gx, gy)):
                            state = "menu"
                            paused = False
                            death = False
                            level_completed = False
                    else:
                        if continue_btn_rect.collidepoint((gx, gy)):
                            paused = False
                        elif menu_btn_rect.collidepoint((gx, gy)):
                            state = "menu"
                            paused = False
                            death = False
                            level_completed = False

        if not paused:
            keys_pressed = pygame.key.get_pressed()
            thin.speed_x = 0
            fat.speed_x = 0
            if keys_pressed[pygame.K_a]:
                thin.speed_x = -thin.speed
            if keys_pressed[pygame.K_d]:
                thin.speed_x = thin.speed
            if keys_pressed[pygame.K_w] and thin.on_ground:
                thin.vel_y = thin.jump_strength
                thin.on_ground = False
            if keys_pressed[pygame.K_LEFT]:
                fat.speed_x = -fat.speed
            if keys_pressed[pygame.K_RIGHT]:
                fat.speed_x = fat.speed
            if keys_pressed[pygame.K_UP] and fat.on_ground:
                fat.vel_y = fat.jump_strength
                fat.on_ground = False

            thin.update(platforms, blocks)
            fat.update(platforms, blocks)
            for block in blocks:
                block.update(platforms)

            for key_rect in keys[:]:
                if thin.rect.colliderect(key_rect) and not thin.has_key:
                    thin.has_key = True
                    keys.remove(key_rect)
                elif fat.rect.colliderect(key_rect) and not fat.has_key:
                    fat.has_key = True
                    keys.remove(key_rect)

            for door_rect in doors:
                if (thin.rect.colliderect(door_rect) and thin.has_key) or (
                        fat.rect.colliderect(door_rect) and fat.has_key):
                    paused = True
                    level_completed = True

            for spike in spikes:
                if thin.rect.colliderect(spike) or fat.rect.colliderect(spike):
                    paused = True
                    death = True

        for barr in barriers:
            if barr.active:
                if thin.rect.colliderect(barr.rect):
                    if thin.rect.centerx < barr.rect.centerx:
                        thin.rect.right = barr.rect.left
                    else:
                        thin.rect.left = barr.rect.right
                if fat.rect.colliderect(barr.rect):
                    if fat.rect.centerx < barr.rect.centerx:
                        fat.rect.right = barr.rect.left
                    else:
                        fat.rect.left = barr.rect.right

        for btn in buttons:
            if not btn.activated:
                if fat.rect.colliderect(btn.rect) or any(block.rect.colliderect(btn.rect) for block in blocks):
                    btn.activate()

        for coin in coins[:]:
            if thin.rect.colliderect(coin) or fat.rect.colliderect(coin):
                coins.remove(coin)
                coins_collected += 1

        for i in range(min(len(buttons), len(barriers))):
            if buttons[i].activated:
                barriers[i].active = False
                barriers[i].update(dt)

        for plat in platforms:
            tile = platform_tile
            for x in range(0, plat.width, UNIT_SIZE):
                for y in range(0, plat.height, UNIT_SIZE):
                    game_surface.blit(tile, (plat.x + x, plat.y + y))

        for spike in spikes:
            img = pygame.transform.scale(spike_img, (spike.width, spike.height))
            game_surface.blit(img, spike)

        for key_rect in keys:
            img = pygame.transform.scale(key_img, (key_rect.width, key_rect.height))
            game_surface.blit(img, key_rect)

        for door_rect in doors:
            img = pygame.transform.scale(door_img, (door_rect.width, door_rect.height))
            game_surface.blit(img, door_rect)

        for coin in coins:
            img = pygame.transform.scale(coin_img, (coin.width, coin.height))
            game_surface.blit(img, coin)

        for block in blocks:
            block.draw(game_surface)

        thin.draw(game_surface)
        fat.draw(game_surface)

        for btn in buttons:
            btn.draw(game_surface)

        for barr in barriers:
            barr.draw(game_surface)

        if thin.has_key:
            key_display = pygame.transform.scale(key_img, (20, 20))
            game_surface.blit(key_display, (thin.rect.centerx - 10, thin.rect.y - 20))

        if fat.has_key:
            key_display = pygame.transform.scale(key_img, (20, 20))
            game_surface.blit(key_display, (fat.rect.centerx - 10, fat.rect.y - 20))

        mx, my = get_game_mouse_pos()
        pause_color = (255, 255, 0) if pause_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
        pause_btn_rect = render_text("Пауза", (BASE_WIDTH - 60, 30), pause_color)

        if paused:
            overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            game_surface.blit(overlay, (0, 0))
            if death or level_completed:
                if level_completed:
                    render_text(f"Уровень пройден! Собрано монет!: {coins_collected}",
                                (BASE_WIDTH // 2, BASE_HEIGHT // 2 - 60), (255, 255, 255))
                restart_color = (255, 255, 0) if restart_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
                restart_btn_rect = render_text("Заново", (BASE_WIDTH // 2, BASE_HEIGHT // 2 - 20), restart_color)
                menu_color = (255, 255, 0) if menu_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
                menu_btn_rect = render_text("Выйти в меню", (BASE_WIDTH // 2, BASE_HEIGHT // 2 + 20), menu_color)
            else:
                continue_color = (255, 255, 0) if continue_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
                continue_btn_rect = render_text("Продолжить", (BASE_WIDTH // 2, BASE_HEIGHT // 2 - 20), continue_color)
                menu_color = (255, 255, 0) if menu_btn_rect.collidepoint((mx, my)) else (255, 255, 255)
                menu_btn_rect = render_text("Выйти в меню", (BASE_WIDTH // 2, BASE_HEIGHT // 2 + 20), menu_color)

        scaled_surface = pygame.transform.scale(game_surface, window_size)
        display_surface.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)
