#!/usr/bin/env python3
import cv2
import socket
import struct
import time
import numpy as np
from picamera2 import Picamera2
from threading import Thread

# Camera Configuration
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (640, 480)},
    controls={"FrameRate": 20}
)
picam2.configure(config)

# UDP Streaming Configuration
UDP_IP = "0.0.0.0"
UDP_PORT = 5000
MAX_CHUNK_SIZE = 1024

class VideoStreamer:
    def __init__(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((UDP_IP, UDP_PORT))
            self.sock.settimeout(0.1)
            self.client_addr = None
            self.frame_id = 0
            print("Video streamer initialized")
        except Exception as e:
            print(f"Video streamer initialization failed: {str(e)}")
            raise

    def start_camera(self):
        print("Starting camera...")
        picam2.start()
        time.sleep(2)  # Camera warm-up time

    def stream(self):
        self.start_camera()
        print("Streaming started")
        
        while True:
            try:
                frame = picam2.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Compress frame to JPEG
                success, jpeg = cv2.imencode('.jpg', frame, 
                                           [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not success:
                    continue
                
                data = jpeg.tobytes()
                data_size = len(data)
                chunks = [data[i:i+MAX_CHUNK_SIZE] 
                         for i in range(0, data_size, MAX_CHUNK_SIZE)]
                
                # Send frame info (frame_id, num_chunks)
                header = struct.pack("II", self.frame_id, len(chunks))
                self.sock.sendto(header, self.client_addr)
                
                # Send chunks
                for i, chunk in enumerate(chunks):
                    chunk_header = struct.pack("II", self.frame_id, i)
                    self.sock.sendto(chunk_header + chunk, self.client_addr)
                
                self.frame_id = (self.frame_id + 1) % 1000000
                
            except Exception as e:
                print(f"Streaming error: {str(e)}")
                time.sleep(0.1)

    def listen(self):
        print("Listening for clients...")
        while True:
            try:
                _, self.client_addr = self.sock.recvfrom(1024)
                print(f"Client connected: {self.client_addr}")
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Listen error: {str(e)}")

    def run(self):
        listen_thread = Thread(target=self.listen, daemon=True)
        listen_thread.start()
        self.stream()

if __name__ == "__main__":
    try:
        streamer = VideoStreamer()
        streamer.run()
    except KeyboardInterrupt:
        print("\nStopping streamer...")
        picam2.stop()