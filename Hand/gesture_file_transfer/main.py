import cv2
import mediapipe as mp
import threading
import os
from utils import broadcast_presence, listen_for_devices, send_file, receive_file, devices_on_network, get_file_from_gallery
from config import STABLE_THRESHOLD, GESTURE_MAP

# ------------------ GESTURE DETECTION ------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

stable_gesture = None
stable_count = 0
last_action = None

def recognize_gesture(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    fingers = []
    # Thumb
    if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0]-1].x:
        fingers.append(1)
    else:
        fingers.append(0)
    # Other fingers
    for i in range(1,5):
        if hand_landmarks.landmark[tips[i]].y < hand_landmarks.landmark[tips[i]-2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    total = fingers.count(1)
    if total == 5:
        return "FIVE"
    elif total == 0:
        return "FIST"
    elif fingers[0] and not any(fingers[1:]):
        return "THUMB_UP"
    elif fingers[1] and fingers[2] and not fingers[0] and not fingers[3] and not fingers[4]:
        return "PEACE"
    else:
        return "UNKNOWN"

def gesture_loop():
    global stable_gesture, stable_count, last_action
    cap = cv2.VideoCapture(0)
    print("Gesture detection running... Show gestures to control file transfer.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame,1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        gesture = "UNKNOWN"

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
                gesture = recognize_gesture(handLms)

        # Stability check
        if gesture == stable_gesture:
            stable_count += 1
        else:
            stable_gesture = gesture
            stable_count = 0
            last_action = None

        # Check for gesture actions
        if stable_count > STABLE_THRESHOLD and gesture in GESTURE_MAP:
            action = GESTURE_MAP[gesture]
            if action != last_action:
                last_action = action
                if action == "SELECT":
                    print("Do you want to continue? Show CONFIRM gesture.")
                elif action == "CONFIRM":
                    print("Gallery opened. Select your file.")
                elif action == "SEND":
                    if devices_on_network:
                        target = devices_on_network[0]  # send to first detected device
                        file_path = get_file_from_gallery()  # open file picker
                        if file_path:
                            send_file(file_path, target)
                            print(f"✅ File sent: {os.path.basename(file_path)}")
                        else:
                            print("❌ No file selected, action cancelled.")
                    else:
                        print("No devices detected on same Wi-Fi.")
                elif action == "CANCEL":
                    print("❌ Action cancelled.")

        # Show gesture on webcam
        cv2.putText(frame, f"Gesture: {gesture}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("Gesture File Transfer", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# ------------------ MAIN ------------------
if __name__ == "__main__":
    # Start networking threads
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_devices, daemon=True).start()
    threading.Thread(target=receive_file, daemon=True).start()

    # Start gesture detection
    gesture_loop()
