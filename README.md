# CHIP-8 Tk GUI Emulator

A simple CHIP-8 emulator written in pure Python with a Tkinter GUI.

## Files
- `main.py` — GUI launcher
- `chip8.py` — emulator core
- `fonts.py` — CHIP-8 font sprites

## Run
```bash
python main.py
```

Or load a ROM directly:

```bash
python main.py roms/Pong.ch8
```

## Controls
Keyboard mapping:

```
1 2 3 4
Q W E R
A S D F
Z X C V
```

The on-screen keypad is clickable too.

## Notes
This version does not use pygame.

It is best run in a graphical environment such as:
- VNC desktop
- X11 desktop
- normal Linux desktop
