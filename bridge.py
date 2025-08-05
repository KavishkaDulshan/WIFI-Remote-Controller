import socket
import serial
from threading import Thread

# UDP Server (for PC)
UDP_IP = "0.0.0.0"
UDP_PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# UART Setup (for ESP32)
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

# Store last client address
client_addr = None

def udp_to_uart():
    global client_addr
    while True:
        data, addr = sock.recvfrom(1024)
        client_addr = addr
        ser.write(data)
        print(f"PC → ESP32: {data.decode().strip()}")

def uart_to_udp():
    while True:
        if ser.in_waiting:
            data = ser.readline().decode().strip()
            if data and client_addr:
                sock.sendto(data.encode(), client_addr)
                print(f"ESP32 → PC: {data}")

# Start threads
Thread(target=udp_to_uart, daemon=True).start()
Thread(target=uart_to_udp, daemon=True).start()

# Keep main thread alive
while True:
    pass