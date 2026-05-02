#!/usr/bin/env python3

import time
import threading
import pygame
from pymavlink import mavutil

# =========================
# CONFIG
# =========================
CONNECTION = 'udp:192.168.2.1:14550'
SEND_RATE = 20

PWM_MIN = 1100
PWM_MAX = 1900
PWM_NEUTRAL = 1500
DEADZONE = 0.05
IGNORE = 65535

# =========================
# STATE
# =========================
rc = {i: PWM_NEUTRAL for i in range(1, 7)}
arm_request = False
disarm_request = False
vehicle_armed = False

# =========================
# HELPERS
# =========================
def axis_to_pwm(v):
    return int(PWM_NEUTRAL + max(-1, min(1, v)) * 400)

def clamp(v):
    return int(max(PWM_MIN, min(PWM_MAX, v)))

def bar(val):
    diff = val - 1500
    size = int(diff / 20)
    if size > 0:
        return ">" * size
    elif size < 0:
        return "<" * abs(size)
    else:
        return "|"

def send_rc(master):
    ch = []
    for i in range(1, 9):
        val = rc.get(i, IGNORE)
        if val is None:
            val = IGNORE
        ch.append(int(val))
    master.mav.rc_channels_override_send(
        master.target_system,
        master.target_component,
        *ch
    )

# =========================
# MAV THREAD
# =========================
def mav_thread(master):
    global arm_request, disarm_request, vehicle_armed

    while True:

        msg = master.recv_match(blocking=False)

        if msg:
            if msg.get_type() == 'HEARTBEAT' and msg.type != mavutil.mavlink.MAV_TYPE_GCS:
                vehicle_armed = bool(
                    msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
                )

        send_rc(master)

        if arm_request:
            print("\nARMING...")
            master.mav.command_long_send(
                master.target_system,
                master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,
                1, 21196, 0,0,0,0,0
            )
            arm_request = False

        if disarm_request:
            print("\nDISARMING...")
            master.mav.command_long_send(
                master.target_system,
                master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,
                0, 0,0,0,0,0,0
            )
            disarm_request = False

        time.sleep(1 / SEND_RATE)

# =========================
# MAIN
# =========================
def main():
    global arm_request, disarm_request

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No controller detected")
        return

    joy = pygame.joystick.Joystick(0)
    joy.init()

    print("Controller:", joy.get_name())
    print("START = ARM | Q = DISARM | Ctrl+C = STOP\n")

    master = mavutil.mavlink_connection(CONNECTION)
    master.wait_heartbeat()
    master.set_mode_apm('MANUAL')

    threading.Thread(target=mav_thread, args=(master,), daemon=True).start()

    try:
        while True:

            for event in pygame.event.get():

                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 7:
                        arm_request = True

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        disarm_request = True

            axes = [joy.get_axis(i) for i in range(joy.get_numaxes())]

            # =========================
            # CONTROLS
            # =========================

            rc[6] = axis_to_pwm(axes[0]) if abs(axes[0]) > DEADZONE else PWM_NEUTRAL
            rc[5] = axis_to_pwm(-axes[1]) if abs(axes[1]) > DEADZONE else PWM_NEUTRAL
            rc[4] = axis_to_pwm(axes[2]) if abs(axes[2]) > DEADZONE else PWM_NEUTRAL
            rc[1] = axis_to_pwm(axes[3]) if abs(axes[3]) > DEADZONE else PWM_NEUTRAL

            # Roll (LT/RT)
            lt = axes[4]
            rt = axes[5]
            roll = 0
            if lt > -0.9:
                roll -= (lt + 1) / 2
            if rt > -0.9:
                roll += (rt + 1) / 2
            rc[2] = clamp(1500 + roll * 400)

            # Throttle (LB/RB)
            if joy.get_button(4):
                rc[3] = PWM_MIN
            elif joy.get_button(5):
                rc[3] = PWM_MAX
            else:
                rc[3] = PWM_NEUTRAL

            # =========================
            # PRINT
            # =========================

            if not vehicle_armed:
                print(".", end="", flush=True)

            else:
                movement = []

                if rc[5] > 1520: movement.append("Forward")
                elif rc[5] < 1480: movement.append("Backward")

                if rc[6] > 1520: movement.append("Right")
                elif rc[6] < 1480: movement.append("Left")

                if rc[4] > 1520: movement.append("Yaw Right")
                elif rc[4] < 1480: movement.append("Yaw Left")

                if rc[3] > 1520: movement.append("Up")
                elif rc[3] < 1480: movement.append("Down")

                if rc[2] > 1520: movement.append("Roll Right")
                elif rc[2] < 1480: movement.append("Roll Left")

                if rc[1] > 1520: movement.append("Pitch Down")
                elif rc[1] < 1480: movement.append("Pitch Up")

                print("\n=== STATUS ===")
                print("Movement:", ", ".join(movement) if movement else "Idle")

                for i in range(1,7):
                    print(f"RC{i}: {rc[i]} {bar(rc[i])}")

            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n⚠️ EMERGENCY STOP")

        # stop motors
        for i in range(1,7):
            rc[i] = PWM_NEUTRAL

        for _ in range(10):
            send_rc(master)
            time.sleep(0.05)

        # disarm
        master.mav.command_long_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            0, 0,0,0,0,0,0
        )

        print("✔️ Motors stopped + Disarmed")

        pygame.quit()
        master.close()

# =========================
if __name__ == "__main__":
    main()