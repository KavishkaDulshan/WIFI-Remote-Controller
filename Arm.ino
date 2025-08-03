#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

const char *ssid = "ESP32_Remote";
const char *password = "remote1234";

// Servo configuration
const int SERVO1_PIN = 18;
const int SERVO2_PIN = 19;
Servo servo1;
Servo servo2;
int currentAngle = 90; // Default angle

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
    servo1.attach(SERVO1_PIN);
    servo2.attach(SERVO2_PIN);

    // Set initial position
    servo1.write(currentAngle);
    servo2.write(180 - currentAngle); // Opposite direction
    Serial.println("Servos initialized at 90°");
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

                if (newAngle != currentAngle)
                {
                    currentAngle = newAngle;

                    // Update servos
                    servo1.write(currentAngle);
                    servo2.write(180 - currentAngle); // Reverse for opposite mounted servo

                    Serial.print("Servos set to: ");
                    Serial.print(currentAngle);
                    Serial.print("° and ");
                    Serial.print(180 - currentAngle);
                    Serial.println("°");
                }
            }
        }
    }

    // Small delay to prevent servo jitter
    delay(10);
}