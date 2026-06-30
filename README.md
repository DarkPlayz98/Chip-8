# CHIP-8 Mobile Emulator

A simple CHIP-8 emulator made for Android-friendly Python setups like **Pydroid 3**.

## Files
- `main.py` — launch the emulator
- `chip8.py` — CHIP-8 CPU and memory
- `fonts.py` — built-in CHIP-8 font sprites
- `requirements.txt` — Python dependency list

## How to run

1. Install Python and **pygame**
2. Put a CHIP-8 ROM in the `roms/` folder
3. Run:
   ```bash
   python main.py
   ```

You can also pass a ROM path:

```bash
python main.py roms/Pong.ch8
```

## Controls

Standard CHIP-8 keypad layout:

```
1 2 3 C
4 5 6 D
7 8 9 E
A 0 B F
```

Keyboard mapping:
- `1 2 3 4`
- `Q W E R`
- `A S D F`
- `Z X C V`

Touch input:
- Tap the on-screen buttons.

## Notes

- If no ROM is found, the emulator opens and shows a message.
- The emulator supports the standard CHIP-8 instruction set.
- Sound is optional and depends on your device’s audio support.
