import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from chip8 import Chip8

SCREEN_W = 64
SCREEN_H = 32
SCALE = 10

KEY_MAP = {
    "1": 0x1, "2": 0x2, "3": 0x3, "4": 0xC,
    "q": 0x4, "w": 0x5, "e": 0x6, "r": 0xD,
    "a": 0x7, "s": 0x8, "d": 0x9, "f": 0xE,
    "z": 0xA, "x": 0x0, "c": 0xB, "v": 0xF,
}

BUTTON_LAYOUT = [
    [0x1, 0x2, 0x3, 0xC],
    [0x4, 0x5, 0x6, 0xD],
    [0x7, 0x8, 0x9, 0xE],
    [0xA, 0x0, 0xB, 0xF],
]

HEX_LABELS = {
    0x0: "0", 0x1: "1", 0x2: "2", 0x3: "3",
    0x4: "4", 0x5: "5", 0x6: "6", 0x7: "7",
    0x8: "8", 0x9: "9", 0xA: "A", 0xB: "B",
    0xC: "C", 0xD: "D", 0xE: "E", 0xF: "F",
}


class Chip8App:
    def __init__(self, root, rom_path=None):
        self.root = root
        self.root.title("CHIP-8 Emulator")
        self.root.configure(bg="#15161a")
        self.root.geometry("760x770")
        self.root.minsize(640, 720)

        self.chip8 = Chip8()
        self.running = True
        self.tick_ms = 16
        self.cycles_per_tick = 8

        self._build_ui()
        self._bind_keys()
        self._load_default_rom(rom_path)
        self.root.after(self.tick_ms, self.loop)

    def _build_ui(self):
        top = tk.Frame(self.root, bg="#15161a")
        top.pack(fill="x", padx=12, pady=(12, 6))

        tk.Label(
            top,
            text="CHIP-8 Emulator",
            fg="#dfe7ff",
            bg="#15161a",
            font=("Arial", 18, "bold"),
        ).pack(anchor="w")

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            top,
            textvariable=self.status_var,
            fg="#9fb2d9",
            bg="#15161a",
            font=("Arial", 10),
        ).pack(anchor="w", pady=(4, 0))

        self.canvas = tk.Canvas(
            self.root,
            width=SCREEN_W * SCALE,
            height=SCREEN_H * SCALE,
            bg="#050608",
            highlightthickness=2,
            highlightbackground="#5d6df5",
        )
        self.canvas.pack(padx=12, pady=10)

        buttons = tk.Frame(self.root, bg="#15161a")
        buttons.pack(fill="x", padx=12, pady=6)

        style = {
            "bg": "#23252d",
            "fg": "#eef2ff",
            "activebackground": "#4157d6",
            "activeforeground": "#ffffff",
            "relief": "flat",
            "bd": 0,
            "font": ("Arial", 12, "bold"),
            "height": 2,
            "width": 10,
        }

        tk.Button(buttons, text="Load ROM", command=self.load_rom_dialog, **style).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.pause_btn = tk.Button(buttons, text="Pause", command=self.toggle_pause, **style)
        self.pause_btn.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        tk.Button(buttons, text="Reset", command=self.reset_emulator, **style).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        tk.Button(buttons, text="Step", command=self.single_step, **style).grid(row=0, column=3, padx=4, pady=4, sticky="ew")

        for i in range(4):
            buttons.grid_columnconfigure(i, weight=1)

        tk.Label(
            self.root,
            text="On-screen keypad",
            fg="#dfe7ff",
            bg="#15161a",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=12, pady=(8, 6))

        keypad = tk.Frame(self.root, bg="#15161a")
        keypad.pack(padx=12, pady=(0, 12))

        self.key_buttons = {}
        for r, row in enumerate(BUTTON_LAYOUT):
            for c, key in enumerate(row):
                btn = tk.Button(
                    keypad,
                    text=HEX_LABELS[key],
                    command=lambda k=key: self.press_virtual_key(k),
                    bg="#282b36",
                    fg="#ffffff",
                    activebackground="#5d6df5",
                    activeforeground="#ffffff",
                    relief="flat",
                    bd=0,
                    font=("Arial", 16, "bold"),
                    width=6,
                    height=2,
                )
                btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
                self.key_buttons[key] = btn

        for i in range(4):
            keypad.grid_columnconfigure(i, weight=1)

        self._update_screen()

    def _bind_keys(self):
        self.root.bind("<KeyPress>", self._key_down)
        self.root.bind("<KeyRelease>", self._key_up)

    def _load_default_rom(self, rom_path):
        chosen = rom_path
        if not chosen:
            for path in [Path("roms/Pong.ch8"), Path("roms/IBM_Logo.ch8"), Path("roms/demo.ch8")]:
                if path.exists():
                    chosen = str(path)
                    break

        if chosen and Path(chosen).exists():
            try:
                self.chip8.load_rom_file(chosen)
                self.set_status(f"Loaded ROM: {Path(chosen).name}")
            except Exception as exc:
                self.set_status(f"ROM load failed: {exc}")
        else:
            self.set_status("No ROM loaded. Use Load ROM to choose a file.")

    def set_status(self, text):
        self.status_var.set(text)

    def load_rom_dialog(self):
        path = filedialog.askopenfilename(
            title="Choose CHIP-8 ROM",
            filetypes=[("CHIP-8 ROMs", "*.ch8 *.rom *.bin"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.chip8.load_rom_file(path)
            self.set_status(f"Loaded ROM: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Load failed", str(exc))
            self.set_status(f"Load failed: {exc}")

    def reset_emulator(self):
        self.chip8.reset()
        self.set_status("Emulator reset")

    def toggle_pause(self):
        self.running = not self.running
        self.pause_btn.configure(text="Resume" if not self.running else "Pause")
        self.set_status("Paused" if not self.running else "Running")

    def single_step(self):
        if not self.running:
            self.chip8.cycle()
            self._update_screen()
            self.set_status("Stepped one instruction")

    def press_virtual_key(self, key):
        self.chip8.set_key(key, True)
        self._update_key_visuals()

    def _key_down(self, event):
        key = (event.keysym or "").lower()
        if key in KEY_MAP:
            self.chip8.set_key(KEY_MAP[key], True)
            self._update_key_visuals()
        elif key == "space":
            self.toggle_pause()
        elif key == "r":
            self.reset_emulator()
        elif key == "o":
            self.load_rom_dialog()
        elif key == "n":
            self.single_step()

    def _key_up(self, event):
        key = (event.keysym or "").lower()
        if key in KEY_MAP:
            self.chip8.set_key(KEY_MAP[key], False)
            self._update_key_visuals()

    def _update_key_visuals(self):
        for key, btn in self.key_buttons.items():
            btn.configure(bg="#5d6df5" if self.chip8.keypad[key] else "#282b36")

    def _update_screen(self):
        self.canvas.delete("all")
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                if self.chip8.screen[y][x]:
                    x1 = x * SCALE
                    y1 = y * SCALE
                    self.canvas.create_rectangle(
                        x1, y1, x1 + SCALE, y1 + SCALE,
                        fill="#f3f6ff", outline="#f3f6ff"
                    )
        self.canvas.create_rectangle(0, 0, SCREEN_W * SCALE, SCREEN_H * SCALE, outline="#5d6df5", width=2)

    def loop(self):
        if self.running:
            for _ in range(self.cycles_per_tick):
                self.chip8.cycle()
            self.chip8.tick_timers()

            if self.chip8.get_sound_on():
                self.root.bell()

            self._update_screen()
            self._update_key_visuals()
            self.set_status(
                f"PC={self.chip8.pc:03X}  I={self.chip8.i:03X}  DT={self.chip8.delay_timer:02X}  ST={self.chip8.sound_timer:02X}"
            )

        self.root.after(self.tick_ms, self.loop)


def find_rom_from_args():
    return sys.argv[1] if len(sys.argv) > 1 else None


def main():
    root = tk.Tk()
    Chip8App(root, rom_path=find_rom_from_args())
    root.mainloop()


if __name__ == "__main__":
    main()
