#include <Arduino.h>
#include <ESP32Servo.h>

// Servo configuration
const int SLIDER_SERVO1_PIN = 18;
const int SLIDER_SERVO2_PIN = 19;
const int JOYSTICK_SERVO_PIN = 21;

// UART Configuration
#define RXD2 16 // ESP32 RX pin (connect to Pi TX)
#define TXD2 17 // ESP32 TX pin (connect to Pi RX)

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
unsigned long lastSensorSend = 0;

void setup()
{
    Serial.begin(115200);

    // Initialize UART2 for communication with Raspberry Pi
    Serial2.begin(115200, SERIAL_8N1, RXD2, TXD2);
    Serial.println("UART2 initialized");
    delay(100);

    // Initialize ultrasonic sensor pins
    for (int i = 0; i < NUM_SENSORS; i++)
    {
        pinMode(SENSOR_PINS[i][0], OUTPUT);
        pinMode(SENSOR_PINS[i][1], INPUT);
        digitalWrite(SENSOR_PINS[i][0], LOW);
    }

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
    // Format: "SENSORS:12.3,24.5,18.7"
    String data = "SENSORS:";
    data += String(dist1, 1);
    data += ",";
    data += String(dist2, 1);
    data += ",";
    data += String(dist3, 1);
    data += "\n"; // Important: Add newline terminator

    // Send via UART to Raspberry Pi
    Serial2.print(data);
}

void processCommand(String command)
{
    // Process slider commands
    if (command.startsWith("SLIDER_"))
    {
        int newAngle = command.substring(7).toInt();
        newAngle = constrain(newAngle, 0, 180);

        if (newAngle != sliderAngle)
        {
            sliderAngle = newAngle;
            sliderServo1.write(sliderAngle);
            sliderServo2.write(180 - sliderAngle);
            Serial.print("Slider set to: ");
            Serial.println(sliderAngle);
        }
    }
    // Process joystick servo commands
    else if (command.startsWith("JOY_SERVO_"))
    {
        int newAngle = command.substring(10).toInt();
        newAngle = constrain(newAngle, 0, 180);

        if (newAngle != joystickServoAngle)
        {
            joystickServoAngle = newAngle;
            joystickServo.write(joystickServoAngle);
            Serial.print("Joystick servo set to: ");
            Serial.println(joystickServoAngle);
        }
    }
}

void loop()
{
    // Check for UART commands from Raspberry Pi
    while (Serial2.available())
    {
        String command = Serial2.readStringUntil('\n');
        command.trim(); // Remove any trailing whitespace

        if (command.length() > 0)
        {
            Serial.print("Received command: ");
            Serial.println(command);
            processCommand(command);
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

        // Send to Raspberry Pi
        sendSensorData(distances[0], distances[1], distances[2]);
    }

    delay(10);
}