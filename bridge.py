import socket
import serial
from threading import Thread

UART_PORT = '/dev/ttyS0'
BAUDRATE = 115200
UDP_IP = '0.0.0.0'
UDP_PORT = 12345

def main():
    ser = serial.Serial(UART_PORT, BAUDRATE, timeout=1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(1.0)
    pc_address = None

    def udp_to_serial():
        nonlocal pc_address
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                pc_address = addr
                ser.write(data + b'\n')
                print(f"UDP->UART: {data}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"UDP error: {e}")

    def serial_to_udp():
        while True:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line and pc_address:
                    sock.sendto(line.encode(), pc_address)
                    print(f"UART->UDP: {line}")
            except Exception as e:
                print(f"UART error: {e}")

    Thread(target=udp_to_serial, daemon=True).start()
    Thread(target=serial_to_udp, daemon=True).start()
    print("Bridge running. Press Ctrl+C to stop.")
    try:
        while True: 
            pass
    except KeyboardInterrupt:
        sock.close()
        ser.close()

if __name__ == "__main__":
    main()