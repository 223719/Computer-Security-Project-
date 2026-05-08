import socket
import threading
import tkinter as tk
from tkinter import ttk
import pyaudio
import time
from utils import encrypt, generate_hash

HOST = "127.0.0.1"
TEXT_PORT = 6000
AUDIO_PORT = 7000

# ---------- SOCKETS ----------
text_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
text_sock.connect((HOST, TEXT_PORT))

audio_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio_sock.connect((HOST, AUDIO_PORT))

# ---------- AUDIO ----------
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050  # أخف وأنسب للـ LAN

audio = pyaudio.PyAudio()
mic = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                 input=True, frames_per_buffer=CHUNK)

sending_audio = False
voice_start_time = None

def audio_loop():
    global sending_audio
    while True:
        if sending_audio:
            try:
                data = mic.read(CHUNK, exception_on_overflow=False)
                audio_sock.sendall(data)
            except:
                break

# ---------- GUI HELPERS ----------
def create_bubble(parent, text, is_me=True, is_voice=False, duration=None):
    wrap = tk.Frame(parent, bg="#0f172a")
    wrap.pack(fill="x", pady=4, padx=6)

    align = "e" if is_me else "w"
    bubble_bg = "#25D366" if is_me else "#1f2937"  # أخضر واتساب / رمادي
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

    # Auto-scroll
    canvas.update_idletasks()
    canvas.yview_moveto(1.0)

# ---------- WINDOW ----------
root = tk.Tk()
root.title("Secure Chat")
root.geometry("380x520")
root.configure(bg="#0f172a")

# ---------- HEADER ----------
header = tk.Frame(root, bg="#111827", height=44)
header.pack(fill="x")
tk.Label(header, text="🔐 Secure Chat", bg="#111827", fg="white",
         font=("Segoe UI", 11, "bold")).pack(side="left", padx=10, pady=8)

# ---------- CHAT AREA (Canvas + Scroll) ----------
chat_frame = tk.Frame(root, bg="#0f172a")
chat_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(chat_frame, bg="#0f172a", highlightthickness=0)
scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=canvas.yview)
inner = tk.Frame(canvas, bg="#0f172a")

inner.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=inner, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# ---------- INPUT BAR ----------
input_bar = tk.Frame(root, bg="#111827")
input_bar.pack(fill="x", padx=6, pady=6)

entry = tk.Entry(input_bar, font=("Segoe UI", 10))
entry.pack(side="left", fill="x", expand=True, padx=(6, 6), pady=6)

def send_text():
    msg = entry.get().strip()
    if not msg:
        return
    enc = encrypt(msg)
    h = generate_hash(msg)
    packet = enc + "|" + h
    try:
        text_sock.sendall(packet.encode())
        create_bubble(inner, msg, is_me=True)
        entry.delete(0, tk.END)
    except:
        pass

send_btn = tk.Button(input_bar, text="Send", bg="#22c55e", fg="black",
                     activebackground="#16a34a", relief="flat",
                     width=8, command=send_text)
send_btn.pack(side="right", padx=(0, 6), pady=6)

def toggle_voice():
    global sending_audio, voice_start_time
    sending_audio = not sending_audio
    if sending_audio:
        voice_start_time = time.time()
        voice_btn.config(text="Stop 🎙️", bg="#ef4444")
    else:
        voice_btn.config(text="Voice 🎤", bg="#3b82f6")
        if voice_start_time:
            duration = time.time() - voice_start_time
            create_bubble(inner, "", is_me=True, is_voice=True, duration=duration)
            voice_start_time = None

voice_btn = tk.Button(input_bar, text="Voice 🎤", bg="#3b82f6", fg="white",
                      activebackground="#2563eb", relief="flat",
                      width=9, command=toggle_voice)
voice_btn.pack(side="right", padx=(0, 6), pady=6)

# ---------- RECEIVE TEXT ----------
def receive_text():
    while True:
        try:
            data = text_sock.recv(4096)
            if not data:
                break
            # الرد من السيرفر هنا نص عادي
            try:
                txt = data.decode()
                create_bubble(inner, txt, is_me=False)
            except:
                pass
        except:
            break

threading.Thread(target=receive_text, daemon=True).start()
threading.Thread(target=audio_loop, daemon=True).start()

root.mainloop()