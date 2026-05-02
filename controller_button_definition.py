#!/usr/bin/env python3
"""
Xbox Controller Input Inspector
Displays every button, axis, and hat input in real-time.
Run this to identify which button/stick maps to which number,
then tell me your desired mapping and I'll build the pymavlink RC sender.

Requirements:
    pip install pygame
"""

import pygame
import sys

# Xbox controller button names (standard mapping, may vary by OS/driver)
BUTTON_NAMES = {
    0:  "A",
    1:  "B",
    2:  "X",
    3:  "Y",
    4:  "LB  (Left Bumper)",
    5:  "RB  (Right Bumper)",
    6:  "Back / View",
    7:  "Start / Menu",
    8:  "LSB (Left Stick Click)",
    9:  "RSB (Right Stick Click)",
    10: "Xbox/Guide Button",
}

AXIS_NAMES = {
    0: "Left Stick  X  (Left←  Right→)",
    1: "Left Stick  Y  (Up↑    Down↓ ) [inverted: -1=up]",
    2: "LT  Left Trigger  (rest=-1, full=+1)",
    3: "Right Stick X  (Left←  Right→)",
    4: "Right Stick Y  (Up↑    Down↓ ) [inverted: -1=up]",
    5: "RT  Right Trigger (rest=-1, full=+1)",
}

HAT_NAMES = {
    0: "D-Pad  (x,y)  left=(-1,0)  right=(1,0)  up=(0,1)  down=(0,-1)",
}

AXIS_DEADZONE = 0.05  # Ignore tiny noise below this threshold


def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("❌  No controller detected. Connect your Xbox controller and try again.")
        sys.exit(1)

    joy = pygame.joystick.Joystick(0)
    joy.init()

    print("=" * 60)
    print(f"  Controller : {joy.get_name()}")
    print(f"  Buttons    : {joy.get_numbuttons()}")
    print(f"  Axes       : {joy.get_numaxes()}")
    print(f"  Hats       : {joy.get_numhats()}")
    print("=" * 60)
    print("  Press buttons / move sticks / pull triggers to see input.")
    print("  Press Ctrl+C to quit.")
    print("=" * 60)

    clock = pygame.time.Clock()

    try:
        while True:
            for event in pygame.event.get():
                # ── BUTTONS ──────────────────────────────────────────────
                if event.type == pygame.JOYBUTTONDOWN:
                    name = BUTTON_NAMES.get(event.button, f"Button {event.button}")
                    print(f"  🟢 PRESSED   Button {event.button:2d}  →  {name}")

                elif event.type == pygame.JOYBUTTONUP:
                    name = BUTTON_NAMES.get(event.button, f"Button {event.button}")
                    print(f"  🔴 RELEASED  Button {event.button:2d}  →  {name}")

                # ── AXES (Sticks & Triggers) ──────────────────────────────
                elif event.type == pygame.JOYAXISMOTION:
                    val = event.value
                    if abs(val) > AXIS_DEADZONE:
                        name = AXIS_NAMES.get(event.axis, f"Axis {event.axis}")
                        bar = make_bar(val)
                        print(f"  🕹️  AXIS {event.axis}  {bar}  {val:+.3f}   {name}")

                # ── HAT (D-Pad) ───────────────────────────────────────────
                elif event.type == pygame.JOYHATMOTION:
                    if event.value != (0, 0):
                        name = HAT_NAMES.get(event.hat, f"Hat {event.hat}")
                        print(f"  🎮 D-PAD  Hat {event.hat}  value={event.value}   {name}")
                    else:
                        print(f"  🎮 D-PAD  Hat {event.hat}  RELEASED  →  (0, 0)")

            clock.tick(60)

    except KeyboardInterrupt:
        print("\n  Exiting...")
        pygame.quit()


def make_bar(value: float, width: int = 20) -> str:
    """Draw a simple ASCII bar for axis visualization."""
    filled = int(abs(value) * (width // 2))
    if value >= 0:
        bar = " " * (width // 2) + "█" * filled + " " * (width // 2 - filled)
    else:
        bar = " " * (width // 2 - filled) + "█" * filled + " " * (width // 2)
    center = width // 2
    bar = bar[:center] + "|" + bar[center + 1:]
    return f"[{bar}]"


if __name__ == "__main__":
    main()