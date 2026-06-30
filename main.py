import os
import sys
import time
from pathlib import Path

import pygame

from chip8 import Chip8

KEY_MAP = {
    pygame.K_1: 0x1,
    pygame.K_2: 0x2,
    pygame.K_3: 0x3,
    pygame.K_4: 0xC,
    pygame.K_q: 0x4,
    pygame.K_w: 0x5,
    pygame.K_e: 0x6,
    pygame.K_r: 0xD,
    pygame.K_a: 0x7,
    pygame.K_s: 0x8,
    pygame.K_d: 0x9,
    pygame.K_f: 0xE,
    pygame.K_z: 0xA,
    pygame.K_x: 0x0,
    pygame.K_c: 0xB,
    pygame.K_v: 0xF,
}

BUTTON_LAYOUT = [
    [0x1, 0x2, 0x3, 0xC],
    [0x4, 0x5, 0x6, 0xD],
    [0x7, 0x8, 0x9, 0xE],
    [0xA, 0x0, 0xB, 0xF],
]

BUTTON_LABELS = {
    0x0: "0", 0x1: "1", 0x2: "2", 0x3: "3",
    0x4: "4", 0x5: "5", 0x6: "6", 0x7: "7",
    0x8: "8", 0x9: "9", 0xA: "A", 0xB: "B",
    0xC: "C", 0xD: "D", 0xE: "E", 0xF: "F",
}

DISPLAY_SCALE = 8
DISPLAY_W = 64 * DISPLAY_SCALE
DISPLAY_H = 32 * DISPLAY_SCALE

BTN_W = 96
BTN_H = 44
BTN_GAP = 10
GRID_W = BTN_W * 4 + BTN_GAP * 3
GRID_H = BTN_H * 4 + BTN_GAP * 3

MARGIN_X = (DISPLAY_W - GRID_W) // 2
TOP_PAD = 18
GAP_AFTER_DISPLAY = 18

WINDOW_W = DISPLAY_W
WINDOW_H = TOP_PAD + DISPLAY_H + GAP_AFTER_DISPLAY + GRID_H + 18

BG = (18, 18, 22)
PANEL = (30, 30, 40)
PIXEL_ON = (245, 245, 245)
PIXEL_OFF = (20, 20, 25)
TEXT = (230, 230, 240)
ACCENT = (110, 180, 255)
BUTTON = (45, 45, 60)
BUTTON_ACTIVE = (90, 140, 220)


def find_rom_path() -> str | None:
    if len(sys.argv) > 1:
        return sys.argv[1]

    candidates = [
        Path("roms/Pong.ch8"),
        Path("roms/IBM_Logo.ch8"),
        Path("roms") / "demo.ch8",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    rom_folder = Path("roms")
    if rom_folder.exists():
        for ext in ("*.ch8", "*.rom", "*.bin"):
            found = sorted(rom_folder.glob(ext))
            if found:
                return str(found[0])

    return None


def load_beep_sound():
    try:
        import math
        import array

        sample_rate = 44100
        duration = 0.12
        frequency = 880
        n_samples = int(sample_rate * duration)
        buf = array.array("h")

        for i in range(n_samples):
            t = i / sample_rate
            sample = int(15000 * math.sin(2 * math.pi * frequency * t))
            buf.append(sample)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


def draw_text(surface, font, text, pos, color=TEXT):
    img = font.render(text, True, color)
    surface.blit(img, pos)


def draw_keypad(surface, font, chip8: Chip8, button_rects):
    for row in BUTTON_LAYOUT:
        for key in row:
            rect = button_rects[key]
            active = bool(chip8.keypad[key])
            pygame.draw.rect(surface, BUTTON_ACTIVE if active else BUTTON, rect, border_radius=10)
            pygame.draw.rect(surface, ACCENT, rect, width=2, border_radius=10)
            label = BUTTON_LABELS[key]
            img = font.render(label, True, TEXT)
            img_rect = img.get_rect(center=rect.center)
            surface.blit(img, img_rect)


def build_button_rects():
    rects = {}
    start_x = MARGIN_X
    start_y = TOP_PAD + DISPLAY_H + GAP_AFTER_DISPLAY
    for r in range(4):
        for c in range(4):
            key = BUTTON_LAYOUT[r][c]
            x = start_x + c * (BTN_W + BTN_GAP)
            y = start_y + r * (BTN_H + BTN_GAP)
            rects[key] = pygame.Rect(x, y, BTN_W, BTN_H)
    return rects


def main():
    pygame.init()
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
    except Exception:
        pass

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("CHIP-8 Mobile Emulator")
    clock = pygame.time.Clock()

    font_small = pygame.font.SysFont("Arial", 18)
    font_mid = pygame.font.SysFont("Arial", 22, bold=True)
    font_big = pygame.font.SysFont("Arial", 28, bold=True)

    chip8 = Chip8()

    rom_path = find_rom_path()
    rom_name = "No ROM loaded"
    error = None

    if rom_path and os.path.exists(rom_path):
        try:
            chip8.load_rom_file(rom_path)
            rom_name = os.path.basename(rom_path)
        except Exception as exc:
            error = f"Failed to load ROM: {exc}"
    else:
        error = "Put a CHIP-8 ROM in /roms or pass a file path."

    button_rects = build_button_rects()
    sound = load_beep_sound()
    sound_playing = False
    timer_accumulator = 0.0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        timer_accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEY_MAP:
                    chip8.set_key(KEY_MAP[event.key], True)

            elif event.type == pygame.KEYUP:
                if event.key in KEY_MAP:
                    chip8.set_key(KEY_MAP[event.key], False)

            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                pos = event.pos if hasattr(event, "pos") else None
                if pos is None and hasattr(event, "x") and hasattr(event, "y"):
                    pos = (int(event.x * WINDOW_W), int(event.y * WINDOW_H))
                if pos:
                    for key, rect in button_rects.items():
                        if rect.collidepoint(pos):
                            chip8.set_key(key, True)

            elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                pos = event.pos if hasattr(event, "pos") else None
                if pos is None and hasattr(event, "x") and hasattr(event, "y"):
                    pos = (int(event.x * WINDOW_W), int(event.y * WINDOW_H))
                if pos:
                    for key, rect in button_rects.items():
                        if rect.collidepoint(pos):
                            chip8.set_key(key, False)

        for _ in range(chip8.cycles_per_frame):
            chip8.cycle()

        while timer_accumulator >= 1 / 60:
            chip8.tick_timers()
            timer_accumulator -= 1 / 60

        if sound is not None:
            if chip8.get_sound_on() and not sound_playing:
                try:
                    sound.play(loops=-1)
                    sound_playing = True
                except Exception:
                    sound = None
            elif not chip8.get_sound_on() and sound_playing:
                try:
                    sound.stop()
                except Exception:
                    pass
                sound_playing = False

        screen.fill(BG)

        draw_text(screen, font_mid, "CHIP-8 Mobile Emulator", (16, 10), ACCENT)
        draw_text(screen, font_small, f"ROM: {rom_name}", (16, 40))
        draw_text(screen, font_small, f"PC: {chip8.pc:03X}  I: {chip8.i:03X}  DT: {chip8.delay_timer:02X}  ST: {chip8.sound_timer:02X}", (16, 62))

        display_rect = pygame.Rect(0, TOP_PAD, DISPLAY_W, DISPLAY_H)
        pygame.draw.rect(screen, PANEL, display_rect, border_radius=10)
        pygame.draw.rect(screen, ACCENT, display_rect, width=2, border_radius=10)

        screen_surface = pygame.Surface((64, 32))
        screen_surface.fill((0, 0, 0))
        for y in range(32):
            for x in range(64):
                if chip8.screen[y][x]:
                    screen_surface.set_at((x, y), (255, 255, 255))

        scaled = pygame.transform.scale(screen_surface, (DISPLAY_W, DISPLAY_H))
        screen.blit(scaled, (0, TOP_PAD))

        draw_keypad(screen, font_big, chip8, button_rects)

        if error:
            box = pygame.Rect(16, WINDOW_H - 44, WINDOW_W - 32, 28)
            pygame.draw.rect(screen, (70, 35, 35), box, border_radius=8)
            draw_text(screen, font_small, error, (24, WINDOW_H - 40), (255, 205, 205))

        if chip8.waiting_for_key:
            draw_text(screen, font_small, "Waiting for key input...", (16, WINDOW_H - 40), ACCENT)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
