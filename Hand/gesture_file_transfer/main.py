# main_auto.py
import cv2
import mediapipe as mp
import socket
import threading
import os
import time

# ======================
# CONFIGURATION
# ======================
PORT = 5001
BROADCAST_PORT = 5002
BUFFER_SIZE = 4096
SAVE_FOLDER = "received_files"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# ======================
# DEVICE DISCOVERY
# ======================
devices_on_network = []

def broadcast_presence():
    """Broadcast this device's presence via UDP every 2 seconds."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        sock.sendto(b"GESTURE_DEVICE", ('<broadcast>', BROADCAST_PORT))
        time.sleep(2)

def listen_for_devices():
    """Listen for other devices broadcasting presence."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', BROADCAST_PORT))
    while True:
        data, addr = sock.recvfrom(1024)
        ip = addr[0]
        if ip != socket.gethostbyname(socket.gethostname()) and ip not in devices_on_network:
            devices_on_network.append(ip)
            print(f"📡 Device discovered: {ip}")

# ======================
# GESTURE DETECTION SETUP
# ======================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# ======================
# NETWORK FUNCTIONS
# ======================
def send_file(filename):
    if not devices_on_network:
        print("❌ No devices found on the network")
        return
    target_ip = devices_on_network[0]  # Send to first discovered device
    try:
        with socket.socket() as s:
            s.connect((target_ip, PORT))
            with open(filename, "rb") as f:
                while chunk := f.read(BUFFER_SIZE):
                    s.sendall(chunk)
        print(f"✅ File sent to {target_ip}: {filename}")
    except Exception as e:
        print(f"❌ Send error: {e}")

def receive_file():
    try:
        with socket.socket() as s:
            s.bind(("0.0.0.0", PORT))
            s.listen(1)
            print("📡 Waiting for incoming file...")
            conn, addr = s.accept()
            print(f"🔗 Connected to {addr}")
            filename = os.path.join(SAVE_FOLDER, f"received_{int(time.time())}")
            with open(filename, "wb") as f:
                while True:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                    f.write(data)
            conn.close()
            print(f"💾 File saved at {filename}")
    except Exception as e:
        print(f"❌ Receive error: {e}")

# ======================
# GESTURE LOOP
# ======================
def gesture_mode():
    cap = cv2.VideoCapture(0)
    print("✋ Show gestures:\n✌️ Peace = Send file\n🖐️ Open Hand = Receive file\nPress ESC to exit")

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

                # Peace Sign → send file
                if peace_count == 2:
                    filename = input("📁 Enter file path to send: ")
                    if filename and os.path.exists(filename):
                        threading.Thread(target=send_file, args=(filename,)).start()
                    else:
                        print("❌ File not found, try again")

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
