import pygame
import sys
import socket
import math
import numpy as np
import struct
import threading
import time

# Network configuration
RASPBERRY_PI_IP = "192.168.50.1"  # Raspberry Pi AP IP
UDP_PORT = 12345                  # Control port
VIDEO_PORT = 5000                 # Video port

class RemoteController:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1000, 700
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("ESP32 Remote Controller v5")
        
        # Colors
        self.bg_color = (30, 33, 40)
        self.card_color = (45, 49, 58)
        self.accent_color = (86, 98, 112)
        self.primary_color = (97, 175, 239)
        self.success_color = (152, 195, 121)
        self.warning_color = (224, 108, 117)
        self.text_color = (220, 220, 220)
        self.light_text = (180, 180, 200)
        
        # Joystick properties (bottom left)
        self.joy_center = (150, self.height - 150)
        self.joy_radius = 100
        self.knob_radius = 30
        self.knob_pos = list(self.joy_center)
        self.dragging = False
        
        # Slider properties (bottom right)
        self.slider_x = self.width - 150
        self.slider_y = 150
        self.slider_width = 30
        self.slider_height = 350
        self.slider_knob_radius = 18
        self.slider_pos = self.slider_y + self.slider_height // 2
        self.slider_dragging = False
        self.slider_value = 90
        self.last_sent_value = 90
        
        # Status bar at top
        self.status_height = 60
        self.status_rect = pygame.Rect(0, 0, self.width, self.status_height)
        
        # Ultrasonic sensor display
        self.sensor_rect = pygame.Rect(20, 80, 250, 300)  # Vertical rectangle
        self.sensor_values = [0.0, 0.0, 0.0]  # [sensor1, sensor2, sensor3]
        self.sensor_colors = [self.success_color, self.success_color, self.success_color]
        
        # Video display
        self.video_rect = pygame.Rect(self.width - 320 - 20, 80, 320, 240)
        self.current_frame = None
        self.video_running = True
        
        # Connection status
        self.connection_status = "DISCONNECTED"
        self.status_color = self.warning_color
        
        # Keyboard state tracking
        self.key_states = {
            pygame.K_w: False,  # Up
            pygame.K_s: False,  # Down
            pygame.K_a: False,  # Left
            pygame.K_d: False,  # Right
            pygame.K_UP: False,  # Slider increase
            pygame.K_DOWN: False  # Slider decrease
        }
        
        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.header_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.value_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 16)
        
        # UDP socket for control
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.control_address = (RASPBERRY_PI_IP, UDP_PORT)
        
        # Connect to ESP32 via Raspberry Pi
        self.connect_to_esp32()
        
        # Start video thread
        self.video_thread = threading.Thread(target=self.video_receive_thread, daemon=True)
        self.video_thread.start()
    
    def connect_to_esp32(self):
        try:
            # Test connection by sending a ping
            self.control_sock.sendto(b"CONNECT_TEST\n", self.control_address)
            self.connection_status = "CONNECTED"
            self.status_color = self.success_color
            print(f"Connected to Raspberry Pi at {RASPBERRY_PI_IP}:{UDP_PORT}")
        except Exception as e:
            self.connection_status = "DISCONNECTED"
            self.status_color = self.warning_color
            print(f"Connection failed: {str(e)}")
    
    def send_command(self, command):
        try:
            self.control_sock.sendto((command + '\n').encode(), self.control_address)
            if self.connection_status != "CONNECTED":
                self.connection_status = "CONNECTED"
                self.status_color = self.success_color
        except Exception as e:
            self.connection_status = "DISCONNECTED"
            self.status_color = self.warning_color
            print(f"Send error: {str(e)}")
    
    def receive_sensor_data(self):
        try:
            self.control_sock.settimeout(0.01)
            data, addr = self.control_sock.recvfrom(1024)
            if data:
                message = data.decode().strip()
                if message.startswith("SENSORS:"):
                    sensor_data = message.split(":")[1].split(",")
                    if len(sensor_data) == 3:
                        try:
                            self.sensor_values = [float(val) for val in sensor_data]
                            for i in range(3):
                                if 0 < self.sensor_values[i] < 15:
                                    self.sensor_colors[i] = self.warning_color
                                else:
                                    self.sensor_colors[i] = self.success_color
                        except ValueError:
                            print("Invalid sensor data")
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Receive error: {str(e)}")
    
    def video_receive_thread(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 0))
        sock.sendto(b"connect", (RASPBERRY_PI_IP, VIDEO_PORT))
        
        chunks = {}
        expected_chunks = 0
        current_frame_id = 0
        
        while self.video_running:
            try:
                data, _ = sock.recvfrom(65535)
                if len(data) < 8:
                    continue
                
                # Unpack frame header
                frame_id, chunk_id = struct.unpack("II", data[:8])
                
                # New frame
                if chunk_id == 0 and frame_id != current_frame_id:
                    chunks = {}
                    current_frame_id = frame_id
                    frame_header = struct.unpack("II", data[:8])
                    expected_chunks = frame_header[1]
                    chunks[0] = data[8:]
                else:
                    chunks[chunk_id] = data[8:]
                
                # Check if all chunks received
                if len(chunks) == expected_chunks and expected_chunks > 0:
                    # Reconstruct frame
                    frame_data = b"".join([chunks[i] for i in sorted(chunks)])
                    
                    # Decode JPEG
                    try:
                        frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            self.current_frame = frame
                    except Exception as e:
                        print(f"Video decode error: {str(e)}")
                    
                    chunks = {}
                    expected_chunks = 0
            except Exception as e:
                print(f"Video thread error: {str(e)}")
                time.sleep(0.1)

    def draw_interface(self):
        # Background
        self.screen.fill(self.bg_color)
        
        # Draw status bar
        pygame.draw.rect(self.screen, self.card_color, self.status_rect)
        pygame.draw.line(self.screen, (70, 75, 90), (0, self.status_height), 
                         (self.width, self.status_height), 2)
        
        # Draw title and status
        title = self.title_font.render("ESP32 Remote Controller v5", True, self.primary_color)
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 15))
        
        status_text = self.font.render(f"Status: {self.connection_status}", True, self.status_color)
        self.screen.blit(status_text, (20, 20))
        
        ip_text = self.small_font.render(f"IP: {RASPBERRY_PI_IP}:{UDP_PORT}", True, self.light_text)
        self.screen.blit(ip_text, (self.width - 180, 25))
        
        # Draw ultrasonic sensor display
        pygame.draw.rect(self.screen, self.card_color, self.sensor_rect, 0, 5)
        
        # Draw colored borders based on sensor readings
        border_thickness = 8
        pygame.draw.line(self.screen, self.sensor_colors[0], 
                        (self.sensor_rect.left, self.sensor_rect.top),
                        (self.sensor_rect.left, self.sensor_rect.bottom), 
                        border_thickness)
        pygame.draw.line(self.screen, self.sensor_colors[2], 
                        (self.sensor_rect.right, self.sensor_rect.top),
                        (self.sensor_rect.right, self.sensor_rect.bottom), 
                        border_thickness)
        pygame.draw.line(self.screen, self.sensor_colors[1], 
                        (self.sensor_rect.left, self.sensor_rect.bottom),
                        (self.sensor_rect.right, self.sensor_rect.bottom), 
                        border_thickness)
        
        # Draw sensor labels and values
        sensor1_text = self.font.render(f"S1: {self.sensor_values[0]:.1f}cm", True, self.text_color)
        sensor2_text = self.font.render(f"S2: {self.sensor_values[1]:.1f}cm", True, self.text_color)
        sensor3_text = self.font.render(f"S3: {self.sensor_values[2]:.1f}cm", True, self.text_color)
        
        self.screen.blit(sensor1_text, (self.sensor_rect.left + 10, self.sensor_rect.top + 20))
        self.screen.blit(sensor3_text, (self.sensor_rect.right - sensor3_text.get_width() - 10, 
                                       self.sensor_rect.top + 20))
        self.screen.blit(sensor2_text, (self.sensor_rect.centerx - sensor2_text.get_width()//2, 
                                       self.sensor_rect.bottom - 30))
        
        # Draw distance indicator
        dist_text = self.small_font.render("<15cm = RED", True, self.warning_color)
        self.screen.blit(dist_text, (self.sensor_rect.left + 10, self.sensor_rect.bottom - 60))
        
        dist_text2 = self.small_font.render(">15cm = GREEN", True, self.success_color)
        self.screen.blit(dist_text2, (self.sensor_rect.right - dist_text2.get_width() - 10, 
                                     self.sensor_rect.bottom - 60))
        
        # Draw video feed
        pygame.draw.rect(self.screen, self.card_color, self.video_rect, 0, 5)
        video_title = self.header_font.render("Live Camera Feed", True, self.primary_color)
        self.screen.blit(video_title, (self.video_rect.centerx - video_title.get_width()//2, 
                                      self.video_rect.top - 30))
        
        if self.current_frame is not None:
            try:
                frame = pygame.image.frombuffer(
                    self.current_frame.tobytes(), 
                    self.current_frame.shape[1::-1], 
                    "RGB"
                )
                self.screen.blit(frame, self.video_rect)
            except Exception as e:
                print(f"Video display error: {str(e)}")
        
        # Draw joystick (bottom left)
        pygame.draw.circle(self.screen, self.accent_color, self.joy_center, self.joy_radius, 0)
        pygame.draw.circle(self.screen, (70, 75, 90), self.joy_center, self.joy_radius, 3)
        pygame.draw.circle(self.screen, self.primary_color, self.knob_pos, self.knob_radius, 0)
        
        # Draw joystick labels
        w_text = self.font.render("W", True, self.text_color)
        a_text = self.font.render("A", True, self.text_color)
        s_text = self.font.render("S", True, self.text_color)
        d_text = self.font.render("D", True, self.text_color)
        
        self.screen.blit(w_text, (self.joy_center[0] - w_text.get_width()//2, 
                                 self.joy_center[1] - self.joy_radius - 30))
        self.screen.blit(a_text, (self.joy_center[0] - self.joy_radius - 30, 
                                 self.joy_center[1] - a_text.get_height()//2))
        self.screen.blit(s_text, (self.joy_center[0] - s_text.get_width()//2, 
                                 self.joy_center[1] + self.joy_radius + 10))
        self.screen.blit(d_text, (self.joy_center[0] + self.joy_radius + 10, 
                                 self.joy_center[1] - d_text.get_height()//2))
        
        # Draw slider (bottom right)
        pygame.draw.rect(self.screen, self.accent_color, 
                        (self.slider_x - self.slider_width//2, self.slider_y, 
                         self.slider_width, self.slider_height), 0, 10)
        pygame.draw.rect(self.screen, (70, 75, 90), 
                        (self.slider_x - self.slider_width//2, self.slider_y, 
                         self.slider_width, self.slider_height), 2, 10)
        
        # Draw slider knob
        pygame.draw.circle(self.screen, self.primary_color, 
                          (self.slider_x, self.slider_pos), 
                          self.slider_knob_radius, 0)
        pygame.draw.circle(self.screen, (240, 240, 240), 
                          (self.slider_x, self.slider_pos), 
                          self.slider_knob_radius, 2)
        
        # Draw slider value
        value_text = self.value_font.render(f"{self.slider_value}°", True, self.primary_color)
        self.screen.blit(value_text, (self.slider_x - value_text.get_width()//2, 
                                    self.slider_y - 50))
        
        # Draw slider min/max labels
        min_text = self.font.render("0", True, self.text_color)
        max_text = self.font.render("180", True, self.text_color)
        self.screen.blit(min_text, (self.slider_x - self.slider_width//2 - 25, 
                                  self.slider_y + self.slider_height - 10))
        self.screen.blit(max_text, (self.slider_x - self.slider_width//2 - 30, 
                                  self.slider_y - 10))
        
        # Draw arrow key indicators for slider
        up_text = self.font.render("↑", True, self.text_color)
        down_text = self.font.render("↓", True, self.text_color)
        self.screen.blit(up_text, (self.slider_x + 30, self.slider_y - 10))
        self.screen.blit(down_text, (self.slider_x + 30, self.slider_y + self.slider_height - 25))
        
        # Draw control labels
        joystick_label = self.header_font.render("Joystick Control", True, self.primary_color)
        slider_label = self.header_font.render("Slider Control", True, self.primary_color)
        
        self.screen.blit(joystick_label, (self.joy_center[0] - joystick_label.get_width()//2, 
                                         self.joy_center[1] + self.joy_radius + 40))
        self.screen.blit(slider_label, (self.slider_x - slider_label.get_width()//2, 
                                       self.slider_y + self.slider_height + 40))

    def get_joystick_direction(self):
        dx = self.knob_pos[0] - self.joy_center[0]
        dy = self.knob_pos[1] - self.joy_center[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 20:  # Deadzone
            return "CENTER"
        
        angle = math.degrees(math.atan2(dy, dx))
        
        if -45 <= angle < 45:
            return "RIGHT"
        elif 45 <= angle < 135:
            return "DOWN"
        elif -135 <= angle < -45:
            return "UP"
        else:
            return "LEFT"
    
    def set_slider_value(self, value):
        value = max(0, min(180, value))
        
        if value != self.slider_value:
            self.slider_value = value
            self.slider_pos = self.slider_y + self.slider_height * (1 - value/180)
            
            if self.slider_value != self.last_sent_value:
                self.send_command(f"SLIDER_{self.slider_value}")
                self.last_sent_value = self.slider_value

    def set_joystick_servo_value(self, direction):
        if direction == "LEFT":
            new_value = 20
        elif direction == "RIGHT":
            new_value = 160
        else:  # CENTER
            new_value = 90
        
        self.send_command(f"JOY_SERVO_{new_value}")

    def update_joystick_from_keys(self):
        dx, dy = 0, 0
        
        if self.key_states[pygame.K_w]:  # Up
            dy = -1
        if self.key_states[pygame.K_s]:  # Down
            dy = 1
        if self.key_states[pygame.K_a]:  # Left
            dx = -1
        if self.key_states[pygame.K_d]:  # Right
            dx = 1
            
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
            
        self.knob_pos[0] = self.joy_center[0] + dx * self.joy_radius
        self.knob_pos[1] = self.joy_center[1] + dy * self.joy_radius
        
        return self.get_joystick_direction()

    def run(self):
        last_direction = "CENTER"
        clock = pygame.time.Clock()
        
        while True:
            current_direction = None
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.video_running = False
                    pygame.quit()
                    sys.exit()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.video_running = False
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_r:
                        self.connect_to_esp32()
                    
                    if event.key in self.key_states:
                        self.key_states[event.key] = True
                    
                    if event.key == pygame.K_UP:
                        self.set_slider_value(self.slider_value + 1)
                    elif event.key == pygame.K_DOWN:
                        self.set_slider_value(self.slider_value - 1)
                
                elif event.type == pygame.KEYUP:
                    if event.key in self.key_states:
                        self.key_states[event.key] = False
                    
                    if event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                        self.knob_pos = list(self.joy_center)
                        current_direction = "CENTER"
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if math.hypot(mouse_pos[0]-self.joy_center[0], 
                                 mouse_pos[1]-self.joy_center[1]) <= self.joy_radius:
                        self.dragging = True
                    
                    elif math.hypot(mouse_pos[0]-self.slider_x, 
                                   mouse_pos[1]-self.slider_pos) <= self.slider_knob_radius:
                        self.slider_dragging = True
                    
                    elif (abs(mouse_pos[0] - self.slider_x) < self.slider_width//2 and
                          self.slider_y <= mouse_pos[1] <= self.slider_y + self.slider_height):
                        y_pos = mouse_pos[1]
                        value = round(180 * (1 - (y_pos - self.slider_y) / self.slider_height))
                        self.set_slider_value(value)
                        self.slider_dragging = True
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.dragging = False
                    self.slider_dragging = False
                    
                    if not any(self.key_states.values()):
                        self.knob_pos = list(self.joy_center)
                        current_direction = "CENTER"
                
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.dragging:
                        dx = mouse_pos[0] - self.joy_center[0]
                        dy = mouse_pos[1] - self.joy_center[1]
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        if distance > self.joy_radius:
                            scale = self.joy_radius / distance
                            dx *= scale
                            dy *= scale
                        
                        self.knob_pos[0] = self.joy_center[0] + dx
                        self.knob_pos[1] = self.joy_center[1] + dy
                        current_direction = self.get_joystick_direction()
                    
                    elif self.slider_dragging:
                        y_pos = mouse_pos[1]
                        value = round(180 * (1 - (y_pos - self.slider_y) / self.slider_height))
                        self.set_slider_value(value)
            
            if any([self.key_states[k] for k in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]]):
                current_direction = self.update_joystick_from_keys()
            
            if self.key_states[pygame.K_UP]:
                self.set_slider_value(self.slider_value + 1)
            elif self.key_states[pygame.K_DOWN]:
                self.set_slider_value(self.slider_value - 1)
            
            if current_direction and current_direction != last_direction:
                self.set_joystick_servo_value(current_direction)
                last_direction = current_direction
            elif current_direction == "CENTER" and last_direction != "CENTER":
                self.set_joystick_servo_value("CENTER")
            
            self.receive_sensor_data()
            self.draw_interface()
            pygame.display.flip()
            clock.tick(30)

if __name__ == "__main__":
    controller = RemoteController()
    controller.run()