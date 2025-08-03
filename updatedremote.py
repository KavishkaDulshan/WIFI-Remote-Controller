import tkinter as tk
from tkinter import Canvas
import socket
import math

# ESP32 settings
ESP32_IP = "192.168.4.1"
ESP32_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send data to ESP32
def send_data(data):
    try:
        sock.sendto(data.encode(), (ESP32_IP, ESP32_PORT))
        status_label.config(text=f"Sent: {data}")
    except Exception as e:
        status_label.config(text=f"Error: {e}")

# GUI setup
app = tk.Tk()
app.title("ESP32 Wi-Fi Controller")
app.geometry("600x300")
app.configure(bg="#1e1e1e")

# Joystick area
joystick_frame = tk.Frame(app, bg="#1e1e1e")
joystick_frame.pack(side=tk.LEFT, padx=30)

canvas_size = 180
joystick_canvas = Canvas(joystick_frame, width=canvas_size, height=canvas_size, bg="#2c2c2c", highlightthickness=0)
joystick_canvas.pack()

center = canvas_size // 2
radius = 20
stick = joystick_canvas.create_oval(center - radius, center - radius,
                                    center + radius, center + radius,
                                    fill="cyan")

def move_stick(event):
    dx = event.x - center
    dy = event.y - center
    dist = math.hypot(dx, dy)
    max_dist = center - radius
    if dist > max_dist:
        dx *= max_dist / dist
        dy *= max_dist / dist
    x, y = center + dx, center + dy
    joystick_canvas.coords(stick, x - radius, y - radius, x + radius, y + radius)

    if abs(dx) < 10 and abs(dy) < 10:
        send_data("center")
    elif abs(dx) > abs(dy):
        send_data("right" if dx > 0 else "left")
    else:
        send_data("backward" if dy > 0 else "forward")

def reset_stick(event):
    joystick_canvas.coords(stick, center - radius, center - radius,
                           center + radius, center + radius)
    send_data("center")

joystick_canvas.bind("<B1-Motion>", move_stick)
joystick_canvas.bind("<ButtonRelease-1>", reset_stick)
tk.Label(joystick_frame, text="Joystick", fg="white", bg="#1e1e1e").pack(pady=5)

# Arrow buttons
button_frame = tk.Frame(app, bg="#1e1e1e")
button_frame.pack(side=tk.RIGHT, padx=30)

button_style = {"width": 8, "height": 2, "bg": "#007acc", "fg": "white", "font": ("Arial", 12)}

tk.Button(button_frame, text="↑", command=lambda: send_data("forward"), **button_style).grid(row=0, column=1, pady=5)
tk.Button(button_frame, text="←", command=lambda: send_data("left"), **button_style).grid(row=1, column=0, padx=5)
tk.Button(button_frame, text="→", command=lambda: send_data("right"), **button_style).grid(row=1, column=2, padx=5)
tk.Button(button_frame, text="↓", command=lambda: send_data("backward"), **button_style).grid(row=2, column=1, pady=5)

tk.Label(button_frame, text="Buttons", fg="white", bg="#1e1e1e").grid(row=3, column=1, pady=5)

# Status label
status_label = tk.Label(app, text="Ready", fg="lightgreen", bg="#1e1e1e", font=("Arial", 10))
status_label.pack(side=tk.BOTTOM, pady=10)

app.mainloop()
