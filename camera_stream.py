#!/usr/bin/env python3
import socket
import struct
import time
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from threading import Thread

# Optimized settings for Pi 3
WIDTH = 320
HEIGHT = 240
FPS = 10
QUALITY = 50
BUFFER_SIZE = 5  # Reduced buffer size

# UDP Configuration
UDP_IP = "0.0.0.0"
UDP_PORT = 5000

class VideoStreamer:
    def __init__(self):
        # Initialize camera with optimized settings
        self.picam2 = Picamera2()
        config = self.picam2.create_video_configuration(
            main={"size": (WIDTH, HEIGHT)},
            controls={"FrameRate": FPS}
        )
        self.picam2.configure(config)
        
        # Use MJPEG hardware encoder
        self.encoder = MJPEGEncoder(bitrate=800000, quality=QUALITY)
        self.encoder.output = FileOutput(self.udp_output)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.settimeout(0.1)
        self.client_addr = None
        self.last_ping = time.time()
        
        print(f"Camera: {WIDTH}x{HEIGHT}@{FPS}fps")

    def udp_output(self, buffer):
        """Directly output to UDP without Python processing"""
        if self.client_addr:
            try:
                # Split into max UDP-safe chunks
                max_chunk = 1400  # Safe for most networks
                for i in range(0, len(buffer), max_chunk):
                    self.sock.sendto(buffer[i:i+max_chunk], self.client_addr)
            except:
                self.client_addr = None

    def listen(self):
        """Listen for client connections"""
        print("Waiting for client...")
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                if data == b"connect":
                    self.client_addr = addr
                    self.last_ping = time.time()
                    print(f"Client connected: {self.client_addr}")
                    break
            except socket.timeout:
                pass

    def run(self):
        self.listen()
        self.picam2.start_recording(self.encoder, "mjpeg")
        print("Streaming started")
        
        try:
            while True:
                # Maintain connection
                try:
                    # Check for keepalive
                    if time.time() - self.last_ping > 2:
                        self.sock.sendto(b"PING", self.client_addr)
                        self.last_ping = time.time()
                    
                    # Check for client messages
                    data, addr = self.sock.recvfrom(1024)
                    if data == b"alive":
                        self.last_ping = time.time()
                except socket.timeout:
                    pass
                except:
                    self.client_addr = None
                    print("Client disconnected")
                    self.listen()
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.picam2.stop_recording()
            print("Streaming stopped")
        except Exception as e:
            print(f"Streaming error: {str(e)}")
            self.picam2.stop_recording()

if __name__ == "__main__":
    streamer = VideoStreamer()
    streamer.run()