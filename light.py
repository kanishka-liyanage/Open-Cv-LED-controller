import cv2
import serial
import time
import numpy as np
from mediapipe.python.solutions import hands as mp_hands_module
from mediapipe.python.solutions import drawing_utils as mp_draw
from mediapipe.python.solutions.hands import HandLandmark
import tkinter as tk

# --- Serial setup
arduino = serial.Serial('COM5', 9600, timeout=1)
time.sleep(2)
print("✅ Arduino connected on COM5")

# --- MediaPipe setup
hands = mp_hands_module.Hands(max_num_hands=1, min_detection_confidence=0.7)

# --- Get screen size
root = tk.Tk()
SCREEN_W = root.winfo_screenwidth()
SCREEN_H = root.winfo_screenheight()
root.destroy()
print(f"🖥️ Screen: {SCREEN_W}x{SCREEN_H}")

# --- Webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  SCREEN_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_H)
if not cap.isOpened():
    print("❌ Webcam not found!")
    exit()
print("✅ Webcam opened")
print("👆 Point index finger at a button to toggle LED")

# --- Button layout
BTN_COUNT = 4
BTN_W     = 150
BTN_H     = 170
BTN_Y     = int(SCREEN_H * 0.30)
GAP       = 20

buttons = [
    {"label": "YELLOW", "x": GAP * 1 + BTN_W * 0, "y": BTN_Y, "w": BTN_W, "h": BTN_H,
     "color": (0, 215, 255),   "dim": (0, 80, 110),  "on_cmd": b'A', "off_cmd": b'a', "state": False},
    {"label": "GREEN",  "x": GAP * 2 + BTN_W * 1, "y": BTN_Y, "w": BTN_W, "h": BTN_H,
     "color": (0, 210, 90),    "dim": (0, 70, 30),   "on_cmd": b'B', "off_cmd": b'b', "state": False},
    {"label": "BLUE",   "x": GAP * 3 + BTN_W * 2, "y": BTN_Y, "w": BTN_W, "h": BTN_H,
     "color": (220, 80, 0),    "dim": (80, 25, 0),   "on_cmd": b'C', "off_cmd": b'c', "state": False},
    {"label": "WHITE",  "x": GAP * 4 + BTN_W * 3, "y": BTN_Y, "w": BTN_W, "h": BTN_H,
     "color": (240, 240, 240), "dim": (70, 70, 70),  "on_cmd": b'D', "off_cmd": b'd', "state": False},
]

COOLDOWN = 1.0
last_trigger_time = [0] * 4

# -------------------------------------------------------
def draw_rounded_rect(img, x, y, w, h, radius, color, thickness=-1):
    if thickness == -1:
        cv2.rectangle(img, (x + radius, y),         (x + w - radius, y + h),     color, -1)
        cv2.rectangle(img, (x, y + radius),         (x + w, y + h - radius),     color, -1)
        cv2.circle(img,    (x + radius,     y + radius),     radius, color, -1)
        cv2.circle(img,    (x + w - radius, y + radius),     radius, color, -1)
        cv2.circle(img,    (x + radius,     y + h - radius), radius, color, -1)
        cv2.circle(img,    (x + w - radius, y + h - radius), radius, color, -1)
    else:
        cv2.rectangle(img, (x + radius, y),         (x + w - radius, y + h),     color, thickness)
        cv2.rectangle(img, (x, y + radius),         (x + w, y + h - radius),     color, thickness)
        cv2.circle(img,    (x + radius,     y + radius),     radius, color, thickness)
        cv2.circle(img,    (x + w - radius, y + radius),     radius, color, thickness)
        cv2.circle(img,    (x + radius,     y + h - radius), radius, color, thickness)
        cv2.circle(img,    (x + w - radius, y + h - radius), radius, color, thickness)

def dark_overlay(frame, alpha=0.45):
    overlay = np.zeros_like(frame)
    overlay[:] = (10, 10, 20)
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

# -------------------------------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    frame = dark_overlay(frame)

    finger_x, finger_y = -1, -1

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame, hand_landmarks,
                mp_hands_module.HAND_CONNECTIONS
            )
            tip      = hand_landmarks.landmark[HandLandmark.INDEX_FINGER_TIP]
            finger_x = int(tip.x * w)
            finger_y = int(tip.y * h)
            cv2.circle(frame, (finger_x, finger_y), 20, (255, 255, 255), 2)
            cv2.circle(frame, (finger_x, finger_y),  5, (0, 255, 255), -1)

    # --- Buttons
    for i, btn in enumerate(buttons):
        bx, by, bw, bh = btn["x"], btn["y"], btn["w"], btn["h"]
        cx = bx + bw // 2
        on_btn = (bx < finger_x < bx + bw) and (by < finger_y < by + bh)

        # Trigger
        if on_btn:
            now = time.time()
            if now - last_trigger_time[i] > COOLDOWN:
                btn["state"] = not btn["state"]
                last_trigger_time[i] = now
                arduino.write(btn["on_cmd"] if btn["state"] else btn["off_cmd"])
                print(f"💡 {btn['label']} {'ON' if btn['state'] else 'OFF'}")

        active_color = btn["color"] if btn["state"] else btn["dim"]

        # Outer glow when ON
        if btn["state"]:
            glow = tuple(min(255, c // 2) for c in btn["color"])
            draw_rounded_rect(frame, bx - 8, by - 8, bw + 16, bh + 16, 20, glow, -1)

        # Card background
        card_bg = (25, 25, 38) if not btn["state"] else tuple(max(0, c // 6) for c in btn["color"])
        draw_rounded_rect(frame, bx, by, bw, bh, 16, card_bg, -1)

        # Hover
        if on_btn:
            draw_rounded_rect(frame, bx, by, bw, bh, 16, (55, 55, 75), -1)

        # Border
        draw_rounded_rect(frame, bx, by, bw, bh, 16, active_color, 3)

        # LED bulb
        led_r  = int(bw * 0.25)
        led_cy = by + int(bh * 0.38)
        cv2.circle(frame, (cx, led_cy), led_r + 5, tuple(c // 4 for c in active_color), -1)
        cv2.circle(frame, (cx, led_cy), led_r,     active_color, -1)

        # Shine
        if btn["state"]:
            shine = frame.copy()
            cv2.circle(shine, (cx - led_r // 3, led_cy - led_r // 3), led_r // 4, (255, 255, 255), -1)
            frame = cv2.addWeighted(shine, 0.25, frame, 0.75, 0)

        # ON / OFF text
        state_txt   = "ON" if btn["state"] else "OFF"
        state_color = active_color if btn["state"] else (120, 120, 130)
        font_scale  = bw / 160.0
        ts = cv2.getTextSize(state_txt, cv2.FONT_HERSHEY_DUPLEX, font_scale, 2)[0]
        cv2.putText(frame, state_txt,
                    (cx - ts[0] // 2, by + int(bh * 0.72)),
                    cv2.FONT_HERSHEY_DUPLEX, font_scale, state_color, 2)

        # Label
        lbl_scale = bw / 210.0
        ls = cv2.getTextSize(btn["label"], cv2.FONT_HERSHEY_SIMPLEX, lbl_scale, 2)[0]
        cv2.putText(frame, btn["label"],
                    (cx - ls[0] // 2, by + int(bh * 0.90)),
                    cv2.FONT_HERSHEY_SIMPLEX, lbl_scale, active_color, 2)

        # Bottom bar
        bar_y = by + bh - 8
        cv2.rectangle(frame, (bx + 15, bar_y), (bx + bw - 15, bar_y + 4), (40, 40, 55), -1)
        if btn["state"]:
            cv2.rectangle(frame, (bx + 15, bar_y), (bx + bw - 15, bar_y + 4), active_color, -1)

    # --- Header
    cv2.rectangle(frame, (0, 0), (w, 55), (12, 12, 22), -1)
    cv2.line(frame, (0, 55), (w, 55), (45, 45, 65), 2)
    cv2.putText(frame, "SMART LED CONTROL", (20, 38),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, (180, 180, 220), 2)

    active_list  = [b["label"] for b in buttons if b["state"]]
    status_txt   = "ACTIVE: " + "  |  ".join(active_list) if active_list else "ALL OFF"
    status_color = (0, 255, 140) if active_list else (90, 90, 110)
    st = cv2.getTextSize(status_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
    cv2.putText(frame, status_txt, (w - st[0] - 20, 37),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 1)

    # --- Footer
    cv2.rectangle(frame, (0, h - 35), (w, h), (12, 12, 22), -1)
    cv2.line(frame, (0, h - 35), (w, h - 35), (45, 45, 65), 2)
    cv2.putText(frame, "Point index finger at button to toggle   |   Q = Quit",
                (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (90, 90, 110), 1)

    cv2.imshow("Smart LED Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("👋 Quitting...")
        break

# --- Cleanup
for btn in buttons:
    arduino.write(btn["off_cmd"])
cap.release()
cv2.destroyAllWindows()
arduino.close()
print("✅ Closed cleanly")