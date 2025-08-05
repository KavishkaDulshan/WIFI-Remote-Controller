#!/usr/bin/env python3
import socket
import serial
import sys
from threading import Thread

# UDP Configuration (for PC communication)
UDP_IP = "0.0.0.0"
UDP_PORT = 12345

# UART Configuration (for ESP32)
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 115200

class Bridge:
    def __init__(self):
        try:
            # UDP socket for PC communication
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.bind((UDP_IP, UDP_PORT))
            self.udp_sock.settimeout(0.1)
            
            # Serial connection to ESP32
            self.ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUD_RATE,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            
            self.client_addr = None
            print("Bridge initialized successfully")
        except Exception as e:
            print(f"Bridge initialization failed: {str(e)}")
            sys.exit(1)

    def udp_to_serial(self):
        while True:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                self.client_addr = addr
                if data:
                    self.ser.write(data + b'\n')
            except socket.timeout:
                pass
            except Exception as e:
                print(f"UDP to Serial error: {str(e)}")

    def serial_to_udp(self):
        while True:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode().strip()
                    if line and self.client_addr:
                        self.udp_sock.sendto(line.encode(), self.client_addr)
            except Exception as e:
                print(f"Serial to UDP error: {str(e)}")

    def run(self):
        print("Starting bridge threads...")
        udp_thread = Thread(target=self.udp_to_serial, daemon=True)
        serial_thread = Thread(target=self.serial_to_udp, daemon=True)
        
        udp_thread.start()
        serial_thread.start()
        
        try:
            while True:
                pass  # Keep main thread alive
        except KeyboardInterrupt:
            print("\nClosing bridge...")
            self.ser.close()
            self.udp_sock.close()

if __name__ == "__main__":
    bridge = Bridge()
    bridge.run()