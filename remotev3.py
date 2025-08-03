import pygame
import sys
import socket
import math

# WiFi configuration
ESP32_IP = "192.168.4.1"  # ESP32 default AP IP
PORT = 12345

class RemoteController:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1000, 700
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("ESP32 Remote Controller")
        
        # Colors
        self.bg_color = (30, 33, 40)
        self.card_color = (45, 49, 58)
        self.accent_color = (86, 98, 112)
        self.primary_color = (97, 175, 239)
        self.success_color = (152, 195, 121)
        self.warning_color = (224, 108, 117)
        self.text_color = (220, 220, 220)
        self.light_text = (180, 180, 200)
        
        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.header_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.value_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 16)
        
        # Define card areas
        self.cards = {
            "status": pygame.Rect(20, 20, self.width-40, 80),
            "joystick": pygame.Rect(20, 120, 460, 280),
            "slider": pygame.Rect(500, 120, 240, 280),
            "servos": pygame.Rect(760, 120, 220, 280),
            "joystick_servo": pygame.Rect(20, 420, 460, 180),
            "instructions": pygame.Rect(20, 620, self.width-40, 60)
        }
        
        # Joystick properties
        self.joy_center = (
            self.cards["joystick"].centerx, 
            self.cards["joystick"].centery - 20
        )
        self.joy_radius = 90
        self.knob_radius = 30
        self.knob_pos = list(self.joy_center)
        self.dragging = False
        
        # Slider properties
        self.slider_x = self.cards["slider"].centerx
        self.slider_y = self.cards["slider"].top + 60
        self.slider_width = 30
        self.slider_height = 180
        self.slider_knob_radius = 15
        self.slider_pos = self.slider_y + self.slider_height // 2
        self.slider_dragging = False
        self.slider_value = 90  # Start at midpoint (90)
        self.last_sent_value = 90
        
        # Joystick servo properties
        self.joystick_servo_value = 90  # Start at center
        self.joystick_servo_rect = pygame.Rect(
            self.cards["joystick_servo"].left + 30,
            self.cards["joystick_servo"].top + 50,
            self.cards["joystick_servo"].width - 60,
            30
        )
        
        # Servo status
        self.servo1_value = 90
        self.servo2_value = 90
        self.servo3_value = 90
        
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
        
        # UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_address = (ESP32_IP, PORT)
        
        # Key repeat setup
        pygame.key.set_repeat(200, 50)
        
        # Connect to ESP32
        self.connect_to_esp32()
        
    def connect_to_esp32(self):
        try:
            # Test connection by sending a ping
            self.sock.sendto(b"CONNECT_TEST\n", self.udp_address)
            self.connection_status = "CONNECTED"
            self.status_color = self.success_color
            print(f"Connected to ESP32 at {ESP32_IP}:{PORT}")
        except Exception as e:
            self.connection_status = "DISCONNECTED"
            self.status_color = self.warning_color
            print(f"Connection failed: {str(e)}")

    def send_command(self, command):
        try:
            self.sock.sendto((command + '\n').encode(), self.udp_address)
            # Update connection status to active
            if self.connection_status != "CONNECTED":
                self.connection_status = "CONNECTED"
                self.status_color = self.success_color
        except Exception as e:
            self.connection_status = "DISCONNECTED"
            self.status_color = self.warning_color
            print(f"Send error: {str(e)}")

    def draw_card(self, rect, title, color=None):
        if color is None:
            color = self.card_color
            
        # Draw card background
        pygame.draw.rect(self.screen, color, rect, 0, 10)
        pygame.draw.rect(self.screen, (70, 75, 90), rect, 2, 10)
        
        # Draw card title
        title_surf = self.header_font.render(title, True, self.text_color)
        self.screen.blit(title_surf, (rect.x + 15, rect.y + 10))
        
        return rect

    def draw_interface(self):
        # Background
        self.screen.fill(self.bg_color)
        
        # Draw cards
        self.draw_card(self.cards["status"], "CONNECTION STATUS")
        self.draw_card(self.cards["joystick"], "JOYSTICK CONTROL")
        self.draw_card(self.cards["slider"], "SLIDER CONTROL")
        self.draw_card(self.cards["servos"], "SERVO STATUS")
        self.draw_card(self.cards["joystick_servo"], "JOYSTICK SERVO")
        self.draw_card(self.cards["instructions"], "INSTRUCTIONS")
        
        # Status card content
        status_text = self.font.render(f"Status: {self.connection_status}", True, self.status_color)
        self.screen.blit(status_text, (self.cards["status"].x + 20, self.cards["status"].y + 45))
        
        ip_text = self.small_font.render(f"IP: {ESP32_IP}:{PORT}", True, self.light_text)
        self.screen.blit(ip_text, (self.cards["status"].right - 180, self.cards["status"].y + 50))
        
        # Draw joystick
        pygame.draw.circle(self.screen, self.accent_color, self.joy_center, self.joy_radius, 0)
        pygame.draw.circle(self.screen, (70, 75, 90), self.joy_center, self.joy_radius, 3)
        pygame.draw.circle(self.screen, self.primary_color, self.knob_pos, self.knob_radius, 0)
        
        # Draw joystick labels
        pygame.draw.polygon(self.screen, self.text_color, [
            (self.joy_center[0], self.joy_center[1] - self.joy_radius - 20),
            (self.joy_center[0] - 10, self.joy_center[1] - self.joy_radius),
            (self.joy_center[0] + 10, self.joy_center[1] - self.joy_radius)
        ])
        w_text = self.font.render("W", True, self.text_color)
        self.screen.blit(w_text, (self.joy_center[0] - w_text.get_width()//2, 
                                 self.joy_center[1] - self.joy_radius - 40))
        
        # Draw slider
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
                                    self.slider_y - 40))
        
        # Draw slider min/max labels
        min_text = self.font.render("0", True, self.text_color)
        max_text = self.font.render("180", True, self.text_color)
        self.screen.blit(min_text, (self.slider_x - self.slider_width//2 - 20, 
                                  self.slider_y + self.slider_height - 10))
        self.screen.blit(max_text, (self.slider_x - self.slider_width//2 - 25, 
                                  self.slider_y - 10))
        
        # Draw joystick servo indicator
        pygame.draw.rect(self.screen, self.accent_color, self.joystick_servo_rect, 0, 5)
        pygame.draw.rect(self.screen, (70, 75, 90), self.joystick_servo_rect, 2, 5)
        
        # Draw servo position indicator
        indicator_x = self.joystick_servo_rect.x + (self.joystick_servo_value / 180) * self.joystick_servo_rect.width
        pygame.draw.circle(self.screen, (255, 255, 255), (int(indicator_x), self.joystick_servo_rect.centery), 15, 0)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(indicator_x), self.joystick_servo_rect.centery), 15, 2)
        
        # Draw servo position labels
        servo_text = self.value_font.render(f"{self.joystick_servo_value}°", True, self.primary_color)
        self.screen.blit(servo_text, (self.joystick_servo_rect.centerx - servo_text.get_width()//2, 
                                    self.joystick_servo_rect.y - 40))
        
        # Draw min/max labels for joystick servo
        left_text = self.font.render("20°", True, self.text_color)
        center_text = self.font.render("90°", True, self.text_color)
        right_text = self.font.render("160°", True, self.text_color)
        self.screen.blit(left_text, (self.joystick_servo_rect.x - 25, self.joystick_servo_rect.y + 40))
        self.screen.blit(center_text, (self.joystick_servo_rect.centerx - center_text.get_width()//2, self.joystick_servo_rect.y + 40))
        self.screen.blit(right_text, (self.joystick_servo_rect.right - 35, self.joystick_servo_rect.y + 40))
        
        # Draw servo status
        servo1_text = self.font.render(f"Servo 1: {self.servo1_value}°", True, self.text_color)
        servo2_text = self.font.render(f"Servo 2: {self.servo2_value}°", True, self.text_color)
        servo3_text = self.font.render(f"Servo 3: {self.servo3_value}°", True, self.text_color)
        
        self.screen.blit(servo1_text, (self.cards["servos"].x + 20, self.cards["servos"].y + 50))
        self.screen.blit(servo2_text, (self.cards["servos"].x + 20, self.cards["servos"].y + 90))
        self.screen.blit(servo3_text, (self.cards["servos"].x + 20, self.cards["servos"].y + 130))
        
        # Draw servo visual indicators
        pygame.draw.rect(self.screen, self.accent_color, (self.cards["servos"].x + 150, self.cards["servos"].y + 50, 50, 20), 0, 5)
        pygame.draw.rect(self.screen, self.accent_color, (self.cards["servos"].x + 150, self.cards["servos"].y + 90, 50, 20), 0, 5)
        pygame.draw.rect(self.screen, self.accent_color, (self.cards["servos"].x + 150, self.cards["servos"].y + 130, 50, 20), 0, 5)
        
        # Draw instructions
        instructions = [
            "Joystick: Drag or use W/A/S/D keys",
            "Slider: Drag or use UP/DOWN arrows",
            "Press R to reconnect, ESC to exit"
        ]
        
        for i, text in enumerate(instructions):
            rendered = self.font.render(text, True, self.light_text)
            self.screen.blit(rendered, (self.cards["instructions"].x + 20, 
                                       self.cards["instructions"].y + 20 + i*25))

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
        # Constrain value between 0-180
        value = max(0, min(180, value))
        
        # Update only if value changed
        if value != self.slider_value:
            self.slider_value = value
            self.slider_pos = self.slider_y + self.slider_height * (1 - value/180)
            
            # Update servo values (for display)
            self.servo1_value = value
            self.servo2_value = 180 - value
            
            # Send command if value changed
            if self.slider_value != self.last_sent_value:
                self.send_command(f"SLIDER_{self.slider_value}")
                self.last_sent_value = self.slider_value

    def set_joystick_servo_value(self, direction):
        # Map direction to servo angle
        if direction == "LEFT":
            new_value = 20
        elif direction == "RIGHT":
            new_value = 160
        else:  # CENTER or other
            new_value = 90
        
        # Update if changed
        if new_value != self.joystick_servo_value:
            self.joystick_servo_value = new_value
            self.servo3_value = new_value
            self.send_command(f"JOY_SERVO_{new_value}")

    def update_joystick_from_keys(self):
        # Calculate movement vector from keys
        dx, dy = 0, 0
        
        if self.key_states[pygame.K_w]:  # Up
            dy = -1
        if self.key_states[pygame.K_s]:  # Down
            dy = 1
        if self.key_states[pygame.K_a]:  # Left
            dx = -1
        if self.key_states[pygame.K_d]:  # Right
            dx = 1
            
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/sqrt(2)
            dy *= 0.7071
            
        # Update knob position
        self.knob_pos[0] = self.joy_center[0] + dx * self.joy_radius
        self.knob_pos[1] = self.joy_center[1] + dy * self.joy_radius
        
        # Return direction for sending
        return self.get_joystick_direction()

    def run(self):
        last_direction = "CENTER"
        last_slider_sent = self.slider_value
        
        while True:
            current_direction = None
            slider_changed = False
            
            # Process events
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
                    
                    # Update key states
                    if event.key in self.key_states:
                        self.key_states[event.key] = True
                    
                    # Handle slider keys
                    if event.key == pygame.K_UP:
                        self.set_slider_value(self.slider_value + 1)
                    elif event.key == pygame.K_DOWN:
                        self.set_slider_value(self.slider_value - 1)
                
                elif event.type == pygame.KEYUP:
                    # Update key states
                    if event.key in self.key_states:
                        self.key_states[event.key] = False
                    
                    # Reset joystick when movement keys are released
                    if event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                        self.knob_pos = list(self.joy_center)
                        current_direction = "CENTER"
                
                # Joystick mouse events
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if clicked on joystick
                    if math.hypot(mouse_pos[0]-self.joy_center[0], 
                                 mouse_pos[1]-self.joy_center[1]) <= self.joy_radius:
                        self.dragging = True
                    
                    # Check if clicked on slider knob
                    elif math.hypot(mouse_pos[0]-self.slider_x, 
                                   mouse_pos[1]-self.slider_pos) <= self.slider_knob_radius:
                        self.slider_dragging = True
                    
                    # Check if clicked on slider track
                    elif (abs(mouse_pos[0] - self.slider_x) < self.slider_width//2 and
                          self.slider_y <= mouse_pos[1] <= self.slider_y + self.slider_height):
                        y_pos = mouse_pos[1]
                        value = round(180 * (1 - (y_pos - self.slider_y) / self.slider_height))
                        self.set_slider_value(value)
                        self.slider_dragging = True
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.dragging = False
                    self.slider_dragging = False
                    
                    # Reset joystick to center
                    if not any(self.key_states.values()):
                        self.knob_pos = list(self.joy_center)
                        current_direction = "CENTER"
                
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Handle joystick dragging
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
                    
                    # Handle slider dragging
                    elif self.slider_dragging:
                        y_pos = mouse_pos[1]
                        value = round(180 * (1 - (y_pos - self.slider_y) / self.slider_height))
                        self.set_slider_value(value)
            
            # Handle keyboard joystick control
            if any([self.key_states[k] for k in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]]):
                current_direction = self.update_joystick_from_keys()
            
            # Handle keyboard slider control
            if self.key_states[pygame.K_UP]:
                self.set_slider_value(self.slider_value + 1)
            elif self.key_states[pygame.K_DOWN]:
                self.set_slider_value(self.slider_value - 1)
            
            # Send joystick servo updates
            if current_direction and current_direction != last_direction:
                self.set_joystick_servo_value(current_direction)
                last_direction = current_direction
            elif current_direction == "CENTER" and last_direction != "CENTER":
                self.set_joystick_servo_value("CENTER")
            
            # Draw the interface
            self.draw_interface()
            pygame.display.flip()
            pygame.time.delay(30)

if __name__ == "__main__":
    controller = RemoteController()
    controller.run()