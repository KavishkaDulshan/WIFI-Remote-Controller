#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

const char *ssid = "ESP32_Remote";
const char *password = "remote1234";

// Servo configuration
const int SLIDER_SERVO1_PIN = 18;  // First slider servo
const int SLIDER_SERVO2_PIN = 19;  // Second slider servo
const int JOYSTICK_SERVO_PIN = 21; // Joystick-controlled servo

Servo sliderServo1;
Servo sliderServo2;
Servo joystickServo;

int sliderAngle = 90;        // Current slider value
int joystickServoAngle = 90; // Current joystick servo angle

WiFiUDP udp;

void setup()
{
    Serial.begin(115200);
    delay(100);

    // Create Access Point
    WiFi.softAP(ssid, password);
    IPAddress myIP = WiFi.softAPIP();

    Serial.print("AP IP address: ");
    Serial.println(myIP);

    // Start UDP server
    udp.begin(12345);
    Serial.println("UDP server started");

    // Attach servos
    sliderServo1.attach(SLIDER_SERVO1_PIN);
    sliderServo2.attach(SLIDER_SERVO2_PIN);
    joystickServo.attach(JOYSTICK_SERVO_PIN);

    // Set initial positions
    sliderServo1.write(sliderAngle);
    sliderServo2.write(180 - sliderAngle); // Opposite direction
    joystickServo.write(joystickServoAngle);

    Serial.println("Servos initialized");
    Serial.print("Slider servos: ");
    Serial.print(sliderAngle);
    Serial.print("° and ");
    Serial.print(180 - sliderAngle);
    Serial.println("°");
    Serial.print("Joystick servo: ");
    Serial.print(joystickServoAngle);
    Serial.println("°");
}

void loop()
{
    // Check for UDP packets
    int packetSize = udp.parsePacket();
    if (packetSize)
    {
        // Read packet
        char packetBuffer[packetSize + 1];
        int len = udp.read(packetBuffer, packetSize);
        if (len > 0)
        {
            packetBuffer[len] = '\0'; // Null-terminate

            // Print received command
            Serial.print("Received: ");
            Serial.println(packetBuffer);

            // Process slider commands
            if (strncmp(packetBuffer, "SLIDER_", 7) == 0)
            {
                int newAngle = atoi(packetBuffer + 7);
                newAngle = constrain(newAngle, 0, 180);

                if (newAngle != sliderAngle)
                {
                    sliderAngle = newAngle;

                    // Update slider servos
                    sliderServo1.write(sliderAngle);
                    sliderServo2.write(180 - sliderAngle); // Reverse for opposite mounted servo

                    Serial.print("Slider servos updated: ");
                    Serial.print(sliderAngle);
                    Serial.print("° and ");
                    Serial.print(180 - sliderAngle);
                    Serial.println("°");
                }
            }
            // Process joystick servo commands
            else if (strncmp(packetBuffer, "JOY_SERVO_", 10) == 0)
            {
                int newAngle = atoi(packetBuffer + 10);
                newAngle = constrain(newAngle, 0, 180);

                if (newAngle != joystickServoAngle)
                {
                    joystickServoAngle = newAngle;
                    joystickServo.write(joystickServoAngle);

                    Serial.print("Joystick servo updated: ");
                    Serial.print(joystickServoAngle);
                    Serial.println("°");
                }
            }
        }
    }

    // Small delay to prevent servo jitter
    delay(10);
}