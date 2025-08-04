import pygame
import sys
import socket
import math
import urllib.request
from PIL import Image
import io
from threading import Thread

ESP32_IP = "192.168.10.1"
PORT = 12345

class RemoteController:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1280, 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Boat Controller v2.0")
        
        # Colors
        self.bg_color = (30, 33, 40)
        self.card_color = (45, 49, 58)
        self.primary_color = (97, 175, 239)
        self.success_color = (152, 195, 121)
        self.warning_color = (224, 108, 117)
        self.text_color = (220, 220, 220)
        
        # Joystick
        self.joy_center = (150, self.height - 150)
        self.joy_radius = 100
        self.knob_radius = 30
        self.knob_pos = list(self.joy_center)
        self.dragging = False
        
        # Slider
        self.slider_x = self.width - 150
        self.slider_y = 150
        self.slider_width = 30
        self.slider_height = 350
        self.slider_knob_radius = 18
        self.slider_pos = self.slider_y + self.slider_height // 2
        self.slider_dragging = False
        self.slider_value = 90
        self.last_sent_value = 90
        
        # Status bar
        self.status_height = 60
        self.status_rect = pygame.Rect(0, 0, self.width, self.status_height)
        
        # Sensors
        self.sensor_rect = pygame.Rect(20, 80, 250, 300)
        self.sensor_values = [0.0, 0.0, 0.0]
        self.sensor_colors = [self.success_color] * 3
        
        # Camera
        self.camera_rect = pygame.Rect(self.width - 640 - 20, 80, 640, 480)
        self.camera_surface = None
        self.camera_url = "http://192.168.10.1:8080/?action=stream"
        
        # Connection
        self.connection_status = "DISCONNECTED"
        self.status_color = self.warning_color
        
        # Key states
        self.key_states = {
            pygame.K_w: False, pygame.K_s: False,
            pygame.K_a: False, pygame.K_d: False,
            pygame.K_UP: False, pygame.K_DOWN: False
        }
        
        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.header_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.value_font = pygame.font.SysFont("Arial", 32, bold=True)
        
        # Networking
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_address = (ESP32_IP, PORT)
        self.sock.setblocking(False)
        
        pygame.key.set_repeat(200, 50)
        self.connect_to_esp32()
        self.init_camera()
    
    def init_camera(self):
        try:
            self.camera_thread = Thread(target=self.update_camera)
            self.camera_thread.daemon = True
            self.camera_thread.start()
        except Exception as e:
            print(f"Camera init error: {e}")

    def update_camera(self):
        try:
            stream = urllib.request.urlopen(self.camera_url)
            bytes_data = b''
            while True:
                bytes_data += stream.read(1024)
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    try:
                        img = Image.open(io.BytesIO(jpg))
                        if img.mode != "RGB": 
                            img = img.convert("RGB")
                        img_data = img.tobytes()
                        self.camera_surface = pygame.image.fromstring(
                            img_data, img.size, "RGB")
                    except Exception as e:
                        print(f"Camera decode error: {e}")
        except Exception as e:
            print(f"Camera stream error: {e}")

    def connect_to_esp32(self):
        try:
            self.sock.sendto(b"CONNECT_TEST\n", self.udp_address)
            self.connection_status = "CONNECTED"
            self.status_color = self.success_color
        except Exception as e:
            self.connection_status = "DISCONNECTED"
            self.status_color = self.warning_color

    def send_command(self, command):
        try:
            self.sock.sendto((command + '\n').encode(), self.udp_address)
            if self.connection_status != "CONNECTED":
                self.connection_status = "CONNECTED"
                self.status_color = self.success_color
        except Exception as e:
            self.connection_status = "DISCONNECTED"
            self.status_color = self.warning_color
    
    def receive_sensor_data(self):
        try:
            data, _ = self.sock.recvfrom(1024)
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
                            pass
        except BlockingIOError:
            pass

    def draw_interface(self):
        self.screen.fill(self.bg_color)
        
        # Status bar
        pygame.draw.rect(self.screen, self.card_color, self.status_rect)
        title = self.title_font.render("Boat Controller v2.0", True, self.primary_color)
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 15))
        
        status = self.font.render(f"Status: {self.connection_status}", True, self.status_color)
        self.screen.blit(status, (20, 20))
        
        ip = self.small_font.render(f"IP: {ESP32_IP}:{PORT}", True, self.text_color)
        self.screen.blit(ip, (self.width - 180, 25))
        
        # Sensors
        pygame.draw.rect(self.screen, self.card_color, self.sensor_rect, 0, 5)
        pygame.draw.line(self.screen, self.sensor_colors[0], 
                        (self.sensor_rect.left, self.sensor_rect.top),
                        (self.sensor_rect.left, self.sensor_rect.bottom), 8)
        pygame.draw.line(self.screen, self.sensor_colors[2], 
                        (self.sensor_rect.right, self.sensor_rect.top),
                        (self.sensor_rect.right, self.sensor_rect.bottom), 8)
        pygame.draw.line(self.screen, self.sensor_colors[1], 
                        (self.sensor_rect.left, self.sensor_rect.bottom),
                        (self.sensor_rect.right, self.sensor_rect.bottom), 8)
        
        for i, val in enumerate(self.sensor_values):
            text = self.font.render(f"S{i+1}: {val:.1f}cm", True, self.text_color)
            if i == 0: pos = (self.sensor_rect.left + 10, self.sensor_rect.top + 20)
            elif i == 1: pos = (self.sensor_rect.centerx - text.get_width()//2, self.sensor_rect.bottom - 30)
            else: pos = (self.sensor_rect.right - text.get_width() - 10, self.sensor_rect.top + 20)
            self.screen.blit(text, pos)
        
        # Camera
        if self.camera_surface:
            scaled = pygame.transform.scale(self.camera_surface, 
                                          (self.camera_rect.width, self.camera_rect.height))
            self.screen.blit(scaled, self.camera_rect)
        else:
            pygame.draw.rect(self.screen, self.card_color, self.camera_rect, 0, 5)
            text = self.font.render("Connecting to camera...", True, self.text_color)
            self.screen.blit(text, (self.camera_rect.centerx - text.get_width()//2, 
                                   self.camera_rect.centery - text.get_height()//2))
        
        # Joystick
        pygame.draw.circle(self.screen, (86, 98, 112), self.joy_center, self.joy_radius, 0)
        pygame.draw.circle(self.screen, (70, 75, 90), self.joy_center, self.joy_radius, 3)
        pygame.draw.circle(self.screen, self.primary_color, self.knob_pos, self.knob_radius, 0)
        
        for key, text in zip([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d], ["W", "A", "S", "D"]):
            label = self.font.render(text, True, self.text_color)
            if key == pygame.K_w: pos = (self.joy_center[0] - label.get_width()//2, self.joy_center[1] - self.joy_radius - 30)
            elif key == pygame.K_a: pos = (self.joy_center[0] - self.joy_radius - 30, self.joy_center[1] - label.get_height()//2)
            elif key == pygame.K_s: pos = (self.joy_center[0] - label.get_width()//2, self.joy_center[1] + self.joy_radius + 10)
            else: pos = (self.joy_center[0] + self.joy_radius + 10, self.joy_center[1] - label.get_height()//2)
            self.screen.blit(label, pos)
        
        # Slider
        pygame.draw.rect(self.screen, (86, 98, 112), 
                        (self.slider_x - self.slider_width//2, self.slider_y, 
                         self.slider_width, self.slider_height), 0, 10)
        pygame.draw.rect(self.screen, (70, 75, 90), 
                        (self.slider_x - self.slider_width//2, self.slider_y, 
                         self.slider_width, self.slider_height), 2, 10)
        pygame.draw.circle(self.screen, self.primary_color, 
                          (self.slider_x, self.slider_pos), self.slider_knob_radius, 0)
        
        value = self.value_font.render(f"{self.slider_value}°", True, self.primary_color)
        self.screen.blit(value, (self.slider_x - value.get_width()//2, self.slider_y - 40))
        
        min_text = self.font.render("0", True, self.text_color)
        max_text = self.font.render("180", True, self.text_color)
        self.screen.blit(min_text, (self.slider_x - self.slider_width//2 - 25, self.slider_y + self.slider_height - 10))
        self.screen.blit(max_text, (self.slider_x - self.slider_width//2 - 30, self.slider_y - 10))
        
        up = self.font.render("↑", True, self.text_color)
        down = self.font.render("↓", True, self.text_color)
        self.screen.blit(up, (self.slider_x + 30, self.slider_y - 10))
        self.screen.blit(down, (self.slider_x + 30, self.slider_y + self.slider_height - 25))

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
        else:  # CENTER or other
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
        
        while True:
            current_direction = None
            slider_changed = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
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
            pygame.time.delay(30)

if __name__ == "__main__":
    controller = RemoteController()
    controller.run()