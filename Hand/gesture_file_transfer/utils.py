import socket
import threading
import os

devices_on_network = []
PORT = 5005
BROADCAST_PORT = 5006
BUFFER_SIZE = 4096

def get_local_ip():
    """Get the local IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def broadcast_presence():
    """Broadcast your device’s presence to the network."""
    ip = get_local_ip()
    name = os.getenv("COMPUTERNAME", "Device")
    message = f"{name}:{ip}".encode()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        s.sendto(message, ("<broadcast>", BROADCAST_PORT))

def listen_for_devices():
    """Listen for other devices broadcasting their presence."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", BROADCAST_PORT))

    while True:
        data, addr = s.recvfrom(1024)
        info = data.decode()
        if info not in devices_on_network:
            devices_on_network.append(info)
            print(f"[Device Found] {info}")

def send_file(file_path, target):
    """Send a file to another device."""
    try:
        target_ip = target.split(":")[-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_ip, PORT))

        file_size = os.path.getsize(file_path)
        s.send(os.path.basename(file_path).encode())
        s.recv(1024)  # wait for ack
        s.send(str(file_size).encode())
        s.recv(1024)

        with open(file_path, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                s.sendall(chunk)
        s.close()
        print(f"[Send] ✅ Sent '{file_path}' to {target}")
    except Exception as e:
        print(f"[Send Error] {e}")

def receive_file():
    """Continuously listen for incoming files."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", PORT))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        file_name = conn.recv(1024).decode()
        conn.send(b"ACK")
        file_size = int(conn.recv(1024).decode())
        conn.send(b"ACK")

        with open(file_name, "wb") as f:
            received = 0
            while received < file_size:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                f.write(data)
                received += len(data)
        conn.close()
        print(f"[Receive] ✅ Received '{file_name}' from {addr}")

from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os

def get_file_from_gallery():
    """Open a file picker and return the selected file path."""
    root = Tk()          # Start a hidden window
    root.withdraw()      # Hide the small empty window
    file_path = askopenfilename(title="Select a file to send")  # Open file picker
    root.destroy()       # Close the hidden window
    if file_path:        # If you selected a file
        print(f"[Gallery] You selected: {os.path.basename(file_path)}")
        return file_path
    else:                # If you cancelled
        print("[Gallery] No file selected")
        return None

