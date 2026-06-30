# DarkStation Step 1

This is the first milestone for the new 3D emulator project.

What it does:
- opens a window in VNC
- draws pixels to a framebuffer-style canvas
- animates a simple wireframe cube
- shows FPS and basic controls

What it does not do yet:
- no PlayStation CPU
- no BIOS loading
- no CD-ROM support
- no audio
- no game loading

## Run
```bash
python main.py
```

## Controls
- Space = pause/resume
- R = reset
- F11 = fullscreen
- Esc = quit

## Next step
After this milestone, the next file set will add a real framebuffer abstraction and then the emulator CPU skeleton.
