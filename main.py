import math
import tkinter as tk
from dataclasses import dataclass

WINDOW_W = 960
WINDOW_H = 720
RENDER_W = 320
RENDER_H = 240
SCALE = 3
FRAME_MS = 16


@dataclass
class Vec3:
    x: float
    y: float
    z: float


class StepOneApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DarkStation - Step 1 Display Test")
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.configure(bg="#11131a")
        self.root.minsize(800, 620)

        self.running = True
        self.fullscreen = False
        self.angle = 0.0
        self.frame = 0
        self.fps = 0
        self.fps_counter = 0
        self.fps_clock = 0

        self.pixels = [[0 for _ in range(RENDER_W)] for _ in range(RENDER_H)]

        self.palette = {
            0: "#050608",
            1: "#f5f7ff",
            2: "#6f82ff",
            3: "#ffcf66",
        }

        self._build_ui()
        self._bind_keys()
        self._tick()

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#11131a")
        header.pack(fill="x", padx=12, pady=(12, 8))

        tk.Label(
            header,
            text="DarkStation - Step 1",
            bg="#11131a",
            fg="#eef2ff",
            font=("Arial", 20, "bold"),
        ).pack(anchor="w")

        self.status_var = tk.StringVar(value="Display test online")
        tk.Label(
            header,
            textvariable=self.status_var,
            bg="#11131a",
            fg="#9fb2d9",
            font=("Arial", 10),
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.root, bg="#11131a")
        body.pack(fill="both", expand=True, padx=12, pady=8)

        left = tk.Frame(body, bg="#11131a")
        left.pack(side="left", fill="both", expand=False)

        self.canvas = tk.Canvas(
            left,
            width=RENDER_W * SCALE,
            height=RENDER_H * SCALE,
            bg="#050608",
            highlightthickness=2,
            highlightbackground="#6f82ff",
        )
        self.canvas.pack()

        controls = tk.Frame(left, bg="#11131a")
        controls.pack(fill="x", pady=(10, 0))

        style = {
            "bg": "#252937",
            "fg": "#f2f5ff",
            "activebackground": "#6f82ff",
            "activeforeground": "#ffffff",
            "relief": "flat",
            "bd": 0,
            "font": ("Arial", 11, "bold"),
            "height": 2,
            "width": 12,
        }

        self.btn_pause = tk.Button(controls, text="Pause", command=self.toggle_pause, **style)
        self.btn_pause.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        tk.Button(controls, text="Reset", command=self.reset_scene, **style).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        tk.Button(controls, text="Fullscreen", command=self.toggle_fullscreen, **style).grid(row=0, column=2, padx=4, pady=4, sticky="ew")

        for i in range(3):
            controls.grid_columnconfigure(i, weight=1)

        right = tk.Frame(body, bg="#11131a")
        right.pack(side="right", fill="both", expand=True, padx=(14, 0))

        info = tk.Frame(right, bg="#171a22", highlightthickness=1, highlightbackground="#2f3650")
        info.pack(fill="x", pady=(0, 12))

        tk.Label(
            info,
            text="Milestone 1",
            bg="#171a22",
            fg="#eef2ff",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=10, pady=(10, 2))

        tk.Label(
            info,
            text=(
                "This first build opens a VNC window, draws pixels,\n"
                "animates a simple 3D wireframe object, and shows FPS.\n"
                "It is the display foundation for the emulator."
            ),
            justify="left",
            bg="#171a22",
            fg="#b9c4e2",
            font=("Arial", 10),
        ).pack(anchor="w", padx=10, pady=(0, 10))

        self.metrics_var = tk.StringVar(value="FPS: 0   Frame: 0   Angle: 0.00")
        tk.Label(
            right,
            textvariable=self.metrics_var,
            bg="#11131a",
            fg="#a8c1ff",
            font=("Consolas", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            right,
            text=(
                "Controls:\n"
                "Space = Pause / Resume\n"
                "R = Reset\n"
                "F11 = Fullscreen\n"
                "Esc = Quit"
            ),
            justify="left",
            bg="#11131a",
            fg="#d7def2",
            font=("Arial", 11),
        ).pack(anchor="w")

        self._render_scene()

    def _bind_keys(self):
        self.root.bind("<space>", lambda e: self.toggle_pause())
        self.root.bind("<r>", lambda e: self.reset_scene())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def toggle_pause(self):
        self.running = not self.running
        self.btn_pause.configure(text="Resume" if not self.running else "Pause")
        self.status_var.set("Paused" if not self.running else "Display test online")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def reset_scene(self):
        self.angle = 0.0
        self.frame = 0
        self.fps = 0
        self.fps_counter = 0
        self.fps_clock = 0
        self.status_var.set("Scene reset")

    def clear_pixels(self):
        for y in range(RENDER_H):
            row = self.pixels[y]
            for x in range(RENDER_W):
                row[x] = 0

    def put_pixel(self, x: int, y: int, value: int = 1):
        if 0 <= x < RENDER_W and 0 <= y < RENDER_H:
            self.pixels[y][x] = value

    def draw_line(self, x0, y0, x1, y1, value=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put_pixel(x0, y0, value)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def project(self, point: Vec3):
        distance = 3.5
        scale = 90
        z = point.z + distance
        if z <= 0.1:
            z = 0.1
        px = int(RENDER_W / 2 + (point.x * scale) / z)
        py = int(RENDER_H / 2 - (point.y * scale) / z)
        return px, py

    def rotate_point(self, point: Vec3):
        cy = math.cos(self.angle)
        sy = math.sin(self.angle)
        cx = math.cos(self.angle * 0.7)
        sx = math.sin(self.angle * 0.7)

        x1 = point.x * cy - point.z * sy
        z1 = point.x * sy + point.z * cy

        y2 = point.y * cx - z1 * sx
        z2 = point.y * sx + z1 * cx

        return Vec3(x1, y2, z2)

    def render_checker(self):
        for y in range(0, RENDER_H, 16):
            for x in range(0, RENDER_W, 16):
                shade = 0 if ((x // 16) + (y // 16)) % 2 == 0 else 1
                for yy in range(y, min(y + 16, RENDER_H)):
                    for xx in range(x, min(x + 16, RENDER_W)):
                        if shade == 1 and (xx + yy) % 9 == 0:
                            self.put_pixel(xx, yy, 2)

    def render_scanlines(self):
        for y in range(0, RENDER_H, 4):
            if (y // 4) % 2 == 0:
                for x in range(0, RENDER_W, 11):
                    self.put_pixel(x, y, 2)

    def render_cube(self):
        vertices = [
            Vec3(-1, -1, -1), Vec3(1, -1, -1), Vec3(1, 1, -1), Vec3(-1, 1, -1),
            Vec3(-1, -1, 1), Vec3(1, -1, 1), Vec3(1, 1, 1), Vec3(-1, 1, 1),
        ]
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]

        rotated = []
        for v in vertices:
            rv = self.rotate_point(v)
            rv.x *= 0.9
            rv.y *= 0.9
            rv.z *= 0.9
            rotated.append(rv)

        points = [self.project(v) for v in rotated]
        for a, b in edges:
            x0, y0 = points[a]
            x1, y1 = points[b]
            self.draw_line(x0, y0, x1, y1, 1)

        cx, cy = self.project(Vec3(0, 0, 0))
        for i in range(-2, 3):
            self.put_pixel(cx + i, cy, 3)
            self.put_pixel(cx, cy + i, 3)

    def _render_scene(self):
        self.clear_pixels()
        self.render_checker()
        self.render_scanlines()
        self.render_cube()

    def _draw_to_canvas(self):
        self.canvas.delete("all")
        for y in range(RENDER_H):
            for x in range(RENDER_W):
                value = self.pixels[y][x]
                if value:
                    color = self.palette.get(value, "#f5f7ff")
                    x0 = x * SCALE
                    y0 = y * SCALE
                    self.canvas.create_rectangle(
                        x0,
                        y0,
                        x0 + SCALE,
                        y0 + SCALE,
                        outline=color,
                        fill=color,
                    )
        self.canvas.create_rectangle(0, 0, RENDER_W * SCALE, RENDER_H * SCALE, outline="#6f82ff", width=2)

    def _tick(self):
        if self.running:
            self.angle += 0.035
            self.frame += 1
            self.fps_counter += 1
            self.fps_clock += 1

            if self.fps_clock >= 60:
                self.fps = self.fps_counter
                self.fps_counter = 0
                self.fps_clock = 0

            self._render_scene()
            self._draw_to_canvas()
            self.metrics_var.set(f"FPS: {self.fps:>3}   Frame: {self.frame:>5}   Angle: {self.angle:.2f}")
            self.status_var.set("Display test online")

        self.root.after(FRAME_MS, self._tick)


def main():
    root = tk.Tk()
    StepOneApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
