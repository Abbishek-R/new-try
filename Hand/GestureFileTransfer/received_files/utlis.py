# utlis.py
import socket
import threading
import os
import tkinter as tk
from tkinter import filedialog

devices_on_network = []


# ==============================
# DISCOVERY (Broadcast Presence)
# ==============================
def broadcast_presence():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = b"GESTURE_DEVICE"
    while True:
        s.sendto(message, ("<broadcast>", 50000))
        import time

        time.sleep(5)


# ==============================
# LISTEN FOR OTHER DEVICES
# ==============================
def listen_for_devices():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", 50000))
    while True:
        data, addr = s.recvfrom(1024)
        if data == b"GESTURE_DEVICE" and addr[0] not in devices_on_network:
            devices_on_network.append(addr[0])
            print(f"📡 Device found: {addr[0]}")


# ==============================
# PICK FILE USING FILE DIALOG
# ==============================
def pick_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path


# ==============================
# SEND FILE TO OTHER DEVICES
# ==============================
def send_file(filename, devices):
    if not devices:
        print("❌ No devices found on network")
        return

    for device in devices:
        try:
            s = socket.socket()
            s.connect((device, 60000))
            file_size = os.path.getsize(filename)
            file_name = os.path.basename(filename)
            s.send(f"{file_name}|{file_size}".encode())

            ack = s.recv(1024).decode()
            if ack != "READY":
                s.close()
                continue

            with open(filename, "rb") as f:
                data = f.read(1024)
                while data:
                    s.send(data)
                    data = f.read(1024)

            print(f"✅ File sent successfully to {device}")
            s.close()
        except Exception as e:
            print(f"⚠️ Failed to send to {device}: {e}")


# ==============================
# RECEIVE FILE
# ==============================
def receive_file():
    s = socket.socket()
    s.bind(("", 60000))
    s.listen(1)
    print("📡 Waiting for file...")

    conn, addr = s.accept()
    info = conn.recv(1024).decode()
    filename, filesize = info.split("|")
    filesize = int(filesize)

    conn.send(b"READY")

    os.makedirs("received_files", exist_ok=True)
    filepath = os.path.join("received_files", filename)

    with open(filepath, "wb") as f:
        received = 0
        while received < filesize:
            data = conn.recv(1024)
            if not data:
                break
            f.write(data)
            received += len(data)

    conn.close()
    print(f"✅ File received from {addr[0]} → saved as {filepath}")
