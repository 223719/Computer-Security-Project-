import socket
import threading
import random

HOST = "127.0.0.1"

# TEXT
PORT_IN_TEXT = 6000
PORT_OUT_TEXT = 5000

# AUDIO
PORT_IN_AUDIO = 7000
PORT_OUT_AUDIO = 7001


# ================= MODE =================
print("Select Attack Mode:")
print("1 - Passive (Eavesdropping)")
print("2 - Active (Tampering)")

mode = input("Enter choice: ")

ACTIVE = (mode == "2")


# ================= TEXT =================
def handle_text(sender_conn, receiver_conn):
    while True:
        try:
            data = sender_conn.recv(4096)
            if not data:
                break

            text = data.decode()
            print("[ATTACKER INTERCEPTED TEXT]:", text)

            if ACTIVE:
                # 🔴 تخريب الرسالة → تصبح غير مفهومة
                corrupted = "".join(chr(random.randint(33, 126)) for _ in range(len(text)))
                receiver_conn.send(corrupted.encode())
                print("[ATTACKER MODIFIED TEXT]")
            else:
                # 🟢 تمرير فقط
                receiver_conn.send(data)

        except:
            break


# ================= AUDIO =================
def handle_audio(sender_audio, receiver_audio):
    while True:
        try:
            data = sender_audio.recv(1024)
            if not data:
                break

            if ACTIVE:
                # 🔴 تحويل الصوت إلى Noise
                noise = bytes(random.randint(0, 255) for _ in range(len(data)))
                receiver_audio.send(noise)
                print("[ATTACKER NOISE AUDIO]")
            else:
                # 🟢 تمرير الصوت كما هو
                receiver_audio.send(data)

        except:
            break


# ================= CONNECTIONS =================

# Receiver connections
receiver_text = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver_text.connect((HOST, PORT_OUT_TEXT))

receiver_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver_audio.connect((HOST, PORT_OUT_AUDIO))


# Sender connections
server_text = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_text.bind((HOST, PORT_IN_TEXT))
server_text.listen(1)

print("[ATTACKER] Waiting for TEXT...")
sender_text, _ = server_text.accept()
print("[TEXT CONNECTED]")


server_audio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_audio.bind((HOST, PORT_IN_AUDIO))
server_audio.listen(1)

print("[ATTACKER] Waiting for AUDIO...")
sender_audio, _ = server_audio.accept()
print("[AUDIO CONNECTED]")


# Threads
threading.Thread(target=handle_text, args=(sender_text, receiver_text), daemon=True).start()
threading.Thread(target=handle_audio, args=(sender_audio, receiver_audio), daemon=True).start()


# Keep alive
while True:
    pass