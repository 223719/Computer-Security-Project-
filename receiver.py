import socket
import threading
import tkinter as tk
from tkinter import ttk
import pyaudio
import time
from utils import decrypt, verify_hash

HOST = "127.0.0.1"
TEXT_PORT = 5000
AUDIO_PORT = 7001

# ---------- SOCKETS ----------
text_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
text_server.bind((HOST, TEXT_PORT))
text_server.listen(1)

audio_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio_server.bind((HOST, AUDIO_PORT))
audio_server.listen(1)

print("[Receiver] Waiting for TEXT...")
text_conn, _ = text_server.accept()
print("[Receiver] Waiting for AUDIO...")
audio_conn, _ = audio_server.accept()

# ---------- AUDIO ----------
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050

audio = pyaudio.PyAudio()
spk = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                 output=True, frames_per_buffer=CHUNK)

last_audio_time = 0
audio_active = False
audio_start = None

def audio_receive():
    global last_audio_time, audio_active, audio_start
    while True:
        try:
            data = audio_conn.recv(CHUNK)
            if not data:
                break
            spk.write(data)

            now = time.time()
            if not audio_active:
                audio_active = True
                audio_start = now

            last_audio_time = now
        except:
            break

def audio_monitor():
    global audio_active, audio_start
    while True:
        time.sleep(0.3)
        if audio_active and (time.time() - last_audio_time) > 0.6:
            # انتهاء الرسالة الصوتية
            duration = time.time() - (audio_start or time.time())
            create_bubble(inner, "", is_me=False, is_voice=True, duration=duration)
            audio_active = False
            audio_start = None

# ---------- GUI HELPERS ----------
def create_bubble(parent, text, is_me=True, is_voice=False, duration=None):
    wrap = tk.Frame(parent, bg="#0f172a")
    wrap.pack(fill="x", pady=4, padx=6)

    align = "e" if is_me else "w"
    bubble_bg = "#25D366" if is_me else "#1f2937"
    fg = "black" if is_me else "white"

    cont = tk.Frame(wrap, bg="#0f172a")
    cont.pack(anchor=align)

    bubble = tk.Frame(cont, bg=bubble_bg, bd=0, padx=10, pady=6)
    bubble.pack(anchor=align)

    if is_voice:
        txt = f"🎤 Voice message ({duration:.1f}s)" if duration else "🎤 Voice message"
    else:
        txt = text

    lbl = tk.Label(bubble, text=txt, bg=bubble_bg, fg=fg,
                   font=("Segoe UI", 10), justify="left", wraplength=280)
    lbl.pack()

    canvas.update_idletasks()
    canvas.yview_moveto(1.0)

# ---------- WINDOW ----------
root = tk.Tk()
root.title("Secure Chat")
root.geometry("380x520")
root.configure(bg="#0f172a")

header = tk.Frame(root, bg="#111827", height=44)
header.pack(fill="x")
tk.Label(header, text="🔐 Secure Chat", bg="#111827", fg="white",
         font=("Segoe UI", 11, "bold")).pack(side="left", padx=10, pady=8)

chat_frame = tk.Frame(root, bg="#0f172a")
chat_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(chat_frame, bg="#0f172a", highlightthickness=0)
scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=canvas.yview)
inner = tk.Frame(canvas, bg="#0f172a")

inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=inner, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

input_bar = tk.Frame(root, bg="#111827")
input_bar.pack(fill="x", padx=6, pady=6)

entry = tk.Entry(input_bar, font=("Segoe UI", 10))
entry.pack(side="left", fill="x", expand=True, padx=(6, 6), pady=6)

def send_text():
    msg = entry.get().strip()
    if not msg:
        return
    try:
        text_conn.sendall(msg.encode())
        create_bubble(inner, msg, is_me=True)
        entry.delete(0, tk.END)
    except:
        pass

send_btn = tk.Button(input_bar, text="Send", bg="#22c55e", fg="black",
                     activebackground="#16a34a", relief="flat",
                     width=8, command=send_text)
send_btn.pack(side="right", padx=(0, 6), pady=6)

# ---------- RECEIVE TEXT ----------
def receive_text():
    while True:
        try:
            data = text_conn.recv(4096)
            if not data:
                break
            try:
                s = data.decode()
                enc, h = s.split("|")
                msg = decrypt(enc)
                if verify_hash(msg, h):
                    create_bubble(inner, msg, is_me=False)
                else:
                    create_bubble(inner, "[Tampered]", is_me=False)
            except:
                pass
        except:
            break

threading.Thread(target=receive_text, daemon=True).start()
threading.Thread(target=audio_receive, daemon=True).start()
threading.Thread(target=audio_monitor, daemon=True).start()

root.mainloop()