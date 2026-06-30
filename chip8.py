import random
from dataclasses import dataclass, field

from fonts import FONT_SET


@dataclass
class Chip8:
    memory_size: int = 4096
    start_address: int = 0x200
    display_width: int = 64
    display_height: int = 32
    cycles_per_frame: int = 10

    memory: bytearray = field(default_factory=lambda: bytearray(4096))
    v: list = field(default_factory=lambda: [0] * 16)
    i: int = 0
    pc: int = 0x200
    stack: list = field(default_factory=list)
    delay_timer: int = 0
    sound_timer: int = 0
    keypad: list = field(default_factory=lambda: [0] * 16)
    screen: list = field(default_factory=lambda: [[0] * 64 for _ in range(32)])
    draw_flag: bool = False
    waiting_for_key: bool = False
    wait_register: int = 0

    # Compatibility choices:
    # - shift instructions use VX as the source
    # - Fx55 / Fx65 increment I after transfer
    shift_uses_vx: bool = True
    increment_i_on_loadstore: bool = True

    def __post_init__(self):
        self.reset()

    def reset(self):
        self.memory = bytearray(self.memory_size)
        self.v = [0] * 16
        self.i = 0
        self.pc = self.start_address
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.keypad = [0] * 16
        self.screen = [[0] * self.display_width for _ in range(self.display_height)]
        self.draw_flag = True
        self.waiting_for_key = False
        self.wait_register = 0
        for idx, byte in enumerate(FONT_SET):
            self.memory[idx] = byte

    def load_rom(self, rom_bytes: bytes):
        if len(rom_bytes) + self.start_address > self.memory_size:
            raise ValueError("ROM is too large for CHIP-8 memory.")
        self.reset()
        for idx, byte in enumerate(rom_bytes):
            self.memory[self.start_address + idx] = byte

    def load_rom_file(self, path: str):
        with open(path, "rb") as f:
            self.load_rom(f.read())

    def set_key(self, key: int, pressed: bool):
        if 0 <= key <= 15:
            self.keypad[key] = 1 if pressed else 0
            if pressed and self.waiting_for_key:
                self.v[self.wait_register] = key
                self.waiting_for_key = False
                self.draw_flag = True

    def clear_screen(self):
        self.screen = [[0] * self.display_width for _ in range(self.display_height)]
        self.draw_flag = True

    def tick_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

    def cycle(self):
        if self.waiting_for_key:
            return

        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc = (self.pc + 2) & 0xFFF

        nnn = opcode & 0x0FFF
        n = opcode & 0x000F
        x = (opcode >> 8) & 0x000F
        y = (opcode >> 4) & 0x000F
        kk = opcode & 0x00FF

        top = opcode & 0xF000

        if opcode == 0x00E0:
            self.clear_screen()
            return

        if opcode == 0x00EE:
            if self.stack:
                self.pc = self.stack.pop()
            return

        if top == 0x1000:
            self.pc = nnn
            return

        if top == 0x2000:
            self.stack.append(self.pc)
            self.pc = nnn
            return

        if top == 0x3000:
            if self.v[x] == kk:
                self.pc = (self.pc + 2) & 0xFFF
            return

        if top == 0x4000:
            if self.v[x] != kk:
                self.pc = (self.pc + 2) & 0xFFF
            return

        if top == 0x5000 and n == 0x0:
            if self.v[x] == self.v[y]:
                self.pc = (self.pc + 2) & 0xFFF
            return

        if top == 0x6000:
            self.v[x] = kk
            return

        if top == 0x7000:
            self.v[x] = (self.v[x] + kk) & 0xFF
            return

        if top == 0x8000:
            if n == 0x0:
                self.v[x] = self.v[y]
            elif n == 0x1:
                self.v[x] |= self.v[y]
                self.v[0xF] = 0
            elif n == 0x2:
                self.v[x] &= self.v[y]
                self.v[0xF] = 0
            elif n == 0x3:
                self.v[x] ^= self.v[y]
                self.v[0xF] = 0
            elif n == 0x4:
                total = self.v[x] + self.v[y]
                self.v[0xF] = 1 if total > 0xFF else 0
                self.v[x] = total & 0xFF
            elif n == 0x5:
                self.v[0xF] = 1 if self.v[x] > self.v[y] else 0
                self.v[x] = (self.v[x] - self.v[y]) & 0xFF
            elif n == 0x6:
                if self.shift_uses_vx:
                    self.v[0xF] = self.v[x] & 0x1
                    self.v[x] >>= 1
                else:
                    self.v[0xF] = self.v[y] & 0x1
                    self.v[x] = self.v[y] >> 1
            elif n == 0x7:
                self.v[0xF] = 1 if self.v[y] > self.v[x] else 0
                self.v[x] = (self.v[y] - self.v[x]) & 0xFF
            elif n == 0xE:
                if self.shift_uses_vx:
                    self.v[0xF] = (self.v[x] >> 7) & 0x1
                    self.v[x] = (self.v[x] << 1) & 0xFF
                else:
                    self.v[0xF] = (self.v[y] >> 7) & 0x1
                    self.v[x] = (self.v[y] << 1) & 0xFF
            return

        if top == 0x9000 and n == 0x0:
            if self.v[x] != self.v[y]:
                self.pc = (self.pc + 2) & 0xFFF
            return

        if top == 0xA000:
            self.i = nnn
            return

        if top == 0xB000:
            self.pc = (nnn + self.v[0]) & 0xFFF
            return

        if top == 0xC000:
            self.v[x] = random.randint(0, 255) & kk
            return

        if top == 0xD000:
            self.draw_sprite(self.v[x], self.v[y], n)
            return

        if top == 0xE000:
            if kk == 0x9E:
                if self.keypad[self.v[x] & 0xF]:
                    self.pc = (self.pc + 2) & 0xFFF
            elif kk == 0xA1:
                if not self.keypad[self.v[x] & 0xF]:
                    self.pc = (self.pc + 2) & 0xFFF
            return

        if top == 0xF000:
            if kk == 0x07:
                self.v[x] = self.delay_timer
            elif kk == 0x0A:
                self.waiting_for_key = True
                self.wait_register = x
                self.pc = (self.pc - 2) & 0xFFF
            elif kk == 0x15:
                self.delay_timer = self.v[x]
            elif kk == 0x18:
                self.sound_timer = self.v[x]
            elif kk == 0x1E:
                self.i = (self.i + self.v[x]) & 0xFFF
            elif kk == 0x29:
                self.i = self.v[x] * 5
            elif kk == 0x33:
                value = self.v[x]
                self.memory[self.i] = value // 100
                self.memory[self.i + 1] = (value // 10) % 10
                self.memory[self.i + 2] = value % 10
            elif kk == 0x55:
                for reg in range(x + 1):
                    self.memory[self.i + reg] = self.v[reg]
                if self.increment_i_on_loadstore:
                    self.i = (self.i + x + 1) & 0xFFF
            elif kk == 0x65:
                for reg in range(x + 1):
                    self.v[reg] = self.memory[self.i + reg]
                if self.increment_i_on_loadstore:
                    self.i = (self.i + x + 1) & 0xFFF
            return

    def draw_sprite(self, x_pos: int, y_pos: int, rows: int):
        self.v[0xF] = 0
        for row in range(rows):
            sprite_byte = self.memory[self.i + row]
            for bit in range(8):
                pixel = (sprite_byte >> (7 - bit)) & 1
                if pixel == 0:
                    continue
                x = (x_pos + bit) % self.display_width
                y = (y_pos + row) % self.display_height
                if self.screen[y][x] == 1:
                    self.v[0xF] = 1
                self.screen[y][x] ^= 1
        self.draw_flag = True

    def get_sound_on(self) -> bool:
        return self.sound_timer > 0

    def get_screen(self):
        return self.screen
