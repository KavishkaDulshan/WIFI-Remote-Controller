import tkinter as tk
import socket

# ESP32 Access Point IP and Port
ESP32_IP = "192.168.4.1"  # Default AP IP for ESP32
ESP32_PORT = 8800         # Match with ESP32 UDP port

# UDP Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_data(data):
    try:
        sock.sendto(data.encode(), (ESP32_IP, ESP32_PORT))
        output_label.config(text=f"Sent: {data}")
    except Exception as e:
        output_label.config(text=f"Error: {e}")

# Tkinter GUI
app = tk.Tk()
app.title("ESP32 Control Sender")

app.geometry("300x200")

tk.Label(app, text="Control ESP32", font=("Arial", 16)).pack(pady=10)

tk.Button(app, text="Forward", width=20, command=lambda: send_data("forward")).pack(pady=5)
tk.Button(app, text="Backward", width=20, command=lambda: send_data("backward")).pack(pady=5)
tk.Button(app, text="Left", width=20, command=lambda: send_data("left")).pack(pady=5)
tk.Button(app, text="Right", width=20, command=lambda: send_data("right")).pack(pady=5)

output_label = tk.Label(app, text="", fg="blue")
output_label.pack(pady=10)

app.mainloop()
