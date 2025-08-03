import pygame
import sys
import socket
import math

# WiFi configuration
ESP32_IP = "192.168.4.1"  # ESP32 default AP IP
PORT = 12345

class JoystickController:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("ESP32 Remote Controller")
        
        # Colors
        self.bg_color = (40, 44, 52)
        self.joystick_bg = (86, 98, 112)
        self.joystick_knob = (152, 195, 121)
        self.slider_color = (86, 98, 112)
        self.slider_knob = (97, 175, 239)
        self.joystick_servo_color = (209, 154, 102)
        self.text_color = (220, 220, 220)
        
        # Joystick properties
        self.joy_center = (self.width // 3, self.height // 2)
        self.joy_radius = 100
        self.knob_radius = 40
        self.knob_pos = list(self.joy_center)
        self.dragging = False
        
        # Slider properties
        self.slider_x = 2 * self.width // 3
        self.slider_y = self.height // 2 - 150
        self.slider_width = 30
        self.slider_height = 300
        self.slider_knob_radius = 20
        self.slider_pos = self.slider_y + self.slider_height // 2
        self.slider_dragging = False
        self.slider_value = 90  # Start at midpoint (90)
        self.last_sent_value = 90
        
        # Joystick servo indicator
        self.joystick_servo_value = 90  # Start at center
        self.joystick_servo_rect = pygame.Rect(
            self.width // 3 - 100, 
            self.height // 2 + 150,
            200, 30
        )
        
        # Keyboard state tracking
        self.key_states = {
            pygame.K_w: False,  # Up
            pygame.K_s: False,  # Down
            pygame.K_a: False,  # Left
            pygame.K_d: False,  # Right
            pygame.K_UP: False,  # Slider increase
            pygame.K_DOWN: False  # Slider decrease
        }
        
        # Font
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.value_font = pygame.font.SysFont("Arial", 32, bold=True)
        
        # UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_address = (ESP32_IP, PORT)
        self.connected = True  # UDP doesn't require persistent connection
        
        # Key repeat setup
        pygame.key.set_repeat(200, 50)  # Initial delay: 200ms, repeat every 50ms
        
    def send_command(self, command):
        try:
            self.sock.sendto((command + '\n').encode(), self.udp_address)
        except Exception as e:
            print(f"Send error: {str(e)}")

    def draw_interface(self):
        # Background
        self.screen.fill(self.bg_color)
        
        # Title
        title = self.title_font.render("ESP32 Remote Controller", True, self.text_color)
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 20))
        
        # Connection status
        status = "UDP READY"
        status_color = (152, 195, 121)
        status_text = self.font.render(f"Status: {status}", True, status_color)
        self.screen.blit(status_text, (20, 20))
        
        # Joystick area
        pygame.draw.circle(self.screen, self.joystick_bg, self.joy_center, self.joy_radius, 0)
        pygame.draw.circle(self.screen, self.joystick_bg, self.joy_center, self.joy_radius, 3)
        pygame.draw.circle(self.screen, self.joystick_knob, self.knob_pos, self.knob_radius, 0)
        
        # Draw slider
        pygame.draw.rect(self.screen, self.slider_color, 
                        (self.slider_x - self.slider_width//2, self.slider_y, 
                         self.slider_width, self.slider_height), 0, 10)
        pygame.draw.rect(self.screen, (200, 200, 200), 
                        (self.slider_x - self.slider_width//2, self.slider_y, 
                         self.slider_width, self.slider_height), 3, 10)
        
        # Draw slider knob
        pygame.draw.circle(self.screen, self.slider_knob, 
                          (self.slider_x, self.slider_pos), 
                          self.slider_knob_radius, 0)
        pygame.draw.circle(self.screen, (240, 240, 240), 
                          (self.slider_x, self.slider_pos), 
                          self.slider_knob_radius, 2)
        
        # Draw slider value
        value_text = self.value_font.render(f"Slider: {self.slider_value}°", True, (97, 175, 239))
        self.screen.blit(value_text, (self.slider_x - value_text.get_width()//2, 
                                    self.slider_y - 50))
        
        # Draw slider min/max labels
        min_text = self.font.render("0", True, self.text_color)
        max_text = self.font.render("180", True, self.text_color)
        self.screen.blit(min_text, (self.slider_x - self.slider_width//2 - 30, 
                                  self.slider_y + self.slider_height - 10))
        self.screen.blit(max_text, (self.slider_x - self.slider_width//2 - 40, 
                                  self.slider_y - 10))
        
        # Draw joystick servo indicator
        pygame.draw.rect(self.screen, self.joystick_servo_color, self.joystick_servo_rect, 0, 5)
        pygame.draw.rect(self.screen, (200, 200, 200), self.joystick_servo_rect, 3, 5)
        
        # Draw servo position indicator
        indicator_x = self.joystick_servo_rect.x + (self.joystick_servo_value / 180) * self.joystick_servo_rect.width
        pygame.draw.circle(self.screen, (255, 255, 255), (int(indicator_x), self.joystick_servo_rect.centery), 15, 0)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(indicator_x), self.joystick_servo_rect.centery), 15, 2)
        
        # Draw servo position labels
        servo_text = self.value_font.render(f"Joystick Servo: {self.joystick_servo_value}°", True, self.joystick_servo_color)
        self.screen.blit(servo_text, (self.joystick_servo_rect.centerx - servo_text.get_width()//2, 
                                    self.joystick_servo_rect.y - 40))
        
        # Draw min/max labels for joystick servo
        left_text = self.font.render("20°", True, self.text_color)
        center_text = self.font.render("90°", True, self.text_color)
        right_text = self.font.render("160°", True, self.text_color)
        self.screen.blit(left_text, (self.joystick_servo_rect.x - 30, self.joystick_servo_rect.y + 40))
        self.screen.blit(center_text, (self.joystick_servo_rect.centerx - center_text.get_width()//2, self.joystick_servo_rect.y + 40))
        self.screen.blit(right_text, (self.joystick_servo_rect.right - right_text.get_width() + 30, self.joystick_servo_rect.y + 40))
        
        # Instructions
        instructions = [
            "Joystick: Drag or use W/A/S/D keys (controls servo)",
            "Slider: Drag or use UP/DOWN arrows (controls servos 1-2)",
            "Press ESC to exit"
        ]
        
        for i, text in enumerate(instructions):
            rendered = self.font.render(text, True, (180, 180, 180))
            self.screen.blit(rendered, (20, self.height - 120 + i * 30))

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
    controller = JoystickController()
    controller.run()