#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>

// WiFi configuration
const char *ssid = "ESP32_Remote";
const char *password = "remote1234";

// Servo configuration
const int SLIDER_SERVO1_PIN = 18;
const int SLIDER_SERVO2_PIN = 19;
const int JOYSTICK_SERVO_PIN = 21;

// Ultrasonic sensor configuration
const int NUM_SENSORS = 3;
const int MAX_DISTANCE = 200;

// Sensor pin configuration {trigger, echo}
const int SENSOR_PINS[NUM_SENSORS][2] = {
    {25, 26}, // Sensor 1
    {27, 14}, // Sensor 2
    {12, 13}  // Sensor 3
};

Servo sliderServo1;
Servo sliderServo2;
Servo joystickServo;

int sliderAngle = 90;
int joystickServoAngle = 90;

WiFiUDP udp;
IPAddress remoteIP;
uint16_t remotePort = 0;
unsigned long lastSensorSend = 0;

void setup()
{
    Serial.begin(115200);
    delay(100);

    // Initialize ultrasonic sensor pins
    for (int i = 0; i < NUM_SENSORS; i++)
    {
        pinMode(SENSOR_PINS[i][0], OUTPUT);
        pinMode(SENSOR_PINS[i][1], INPUT);
        digitalWrite(SENSOR_PINS[i][0], LOW);
    }

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
    sliderServo2.write(180 - sliderAngle);
    joystickServo.write(joystickServoAngle);

    Serial.println("System initialized");
}

float measureDistance(int trigPin, int echoPin)
{
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    long duration = pulseIn(echoPin, HIGH);
    float distance = duration * 0.0343 / 2;

    if (distance <= 0 || distance > MAX_DISTANCE)
    {
        return -1.0;
    }

    return distance;
}

void sendSensorData(float dist1, float dist2, float dist3)
{
    if (remotePort == 0)
        return; // No client connected yet

    // Format: "SENSORS:12.3,24.5,18.7"
    String data = "SENSORS:";
    data += String(dist1, 1);
    data += ",";
    data += String(dist2, 1);
    data += ",";
    data += String(dist3, 1);

    // Corrected write method
    udp.beginPacket(remoteIP, remotePort);
    udp.print(data); // Use print() instead of write() for String
    udp.endPacket();
}

void loop()
{
    // Check for UDP packets
    int packetSize = udp.parsePacket();
    if (packetSize)
    {
        // Store client address for sending sensor data
        remoteIP = udp.remoteIP();
        remotePort = udp.remotePort();

        // Read packet
        char packetBuffer[packetSize + 1];
        int len = udp.read(packetBuffer, packetSize);
        if (len > 0)
        {
            packetBuffer[len] = '\0';

            // Process slider commands
            if (strncmp(packetBuffer, "SLIDER_", 7) == 0)
            {
                int newAngle = atoi(packetBuffer + 7);
                newAngle = constrain(newAngle, 0, 180);

                if (newAngle != sliderAngle)
                {
                    sliderAngle = newAngle;
                    sliderServo1.write(sliderAngle);
                    sliderServo2.write(180 - sliderAngle);
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
                }
            }
        }
    }

    // Measure and send sensor data every 300ms
    if (millis() - lastSensorSend >= 300)
    {
        lastSensorSend = millis();

        // Measure all sensors
        float distances[NUM_SENSORS];
        for (int i = 0; i < NUM_SENSORS; i++)
        {
            distances[i] = measureDistance(SENSOR_PINS[i][0], SENSOR_PINS[i][1]);
        }

        // Send to remote
        sendSensorData(distances[0], distances[1], distances[2]);
    }

    delay(10);
}