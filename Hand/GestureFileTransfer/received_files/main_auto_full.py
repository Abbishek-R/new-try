# main_auto_full.py
import threading
import cv2
import mediapipe as mp
from utlis import broadcast_presence, listen_for_devices, pick_file, send_file, receive_file, devices_on_network

# ======================
# GESTURE DETECTION SETUP
# ======================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
# main_auto_full.py
import threading
import cv2
import mediapipe as mp
from utlis import (
    broadcast_presence,
    listen_for_devices,
    pick_file,
    send_file,
    receive_file,
    devices_on_network,
)

# ======================
# GESTURE DETECTION SETUP
# ======================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils


def gesture_mode():
    cap = cv2.VideoCapture(0)
    print("✋ Gesture Controls Active:")
    print("✌️ Peace sign = Send file to all devices")
    print("👉 + 👍 (Index + Thumb) = Receive file")
    print("Press ESC to exit\n")

    send_triggered = False
    receive_triggered = False

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # --- Peace sign detection ---
                peace_count = sum(
                    hand_landmarks.landmark[i].y < hand_landmarks.landmark[i - 2].y
                    for i in [8, 12]
                )

                # --- Thumb + Index for receive ---
                thumb_tip = hand_landmarks.landmark[4]
                thumb_ip = hand_landmarks.landmark[3]
                index_tip = hand_landmarks.landmark[8]
                index_pip = hand_landmarks.landmark[6]

                thumb_up = thumb_tip.x < thumb_ip.x  # adjust for camera mirroring
                index_up = index_tip.y < index_pip.y
                others_down = (
                    sum(
                        hand_landmarks.landmark[i].y
                        < hand_landmarks.landmark[i - 2].y
                        for i in [12, 16, 20]
                    )
                    == 0
                )

                # ✌️ Peace → Send File
                if peace_count == 2 and not send_triggered:
                    send_triggered = True
                    print("📤 Peace gesture detected → Sending file...")
                    filename = pick_file()
                    if filename:
                        threading.Thread(
                            target=send_file, args=(filename, devices_on_network)
                        ).start()
                    else:
                        print("❌ No file selected")

                elif peace_count < 2:
                    send_triggered = False

                # 👍 + 👉 → Receive Mode
                if thumb_up and index_up and others_down and not receive_triggered:
                    receive_triggered = True
                    print("📥 Receive gesture detected → Waiting for incoming file...")
                    threading.Thread(target=receive_file).start()
                elif not (thumb_up and index_up and others_down):
                    receive_triggered = False

        cv2.putText(
            frame,
            "Gesture File Transfer Active",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        cv2.imshow("Gesture File Transfer", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_devices, daemon=True).start()
    gesture_mode()

# ======================
# GESTURE LOOP
# ======================
def gesture_mode():
    cap = cv2.VideoCapture(0)
    print("✋ Show gestures:\n ✌️ Peace = Send file to all devices\n🖐️ Open Hand = Receive file\nPress ESC to exit")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame,1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                fingers = [8, 12, 16, 20]
                up_count = sum(hand_landmarks.landmark[i].y < hand_landmarks.landmark[i-2].y for i in fingers)
                peace_count = sum(hand_landmarks.landmark[i].y < hand_landmarks.landmark[i-2].y for i in [8,12])

                # Peace Sign → pick file automatically and send to all devices
                if peace_count == 2:
                    filename = pick_file()
                    if filename:
                        threading.Thread(target=send_file, args=(filename, devices_on_network)).start()
                    else:
                        print("❌ No file selected")

                # Open Hand → receive file
                elif up_count == 4:
                    threading.Thread(target=receive_file).start()

        cv2.putText(frame, "Gesture Control Active", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("Gesture File Transfer", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_devices, daemon=True).start()
    gesture_mode()
