#include <HardwareSerial.h>
#include <ESP32Servo.h>

// UART Configuration
HardwareSerial SerialPort(0); // Use UART0

// Servo Configuration
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
unsigned long lastSensorSend = 0;

void setup()
{
    SerialPort.begin(115200); // UART communication

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

void loop()
{
    // Read commands from UART
    if (SerialPort.available())
    {
        String command = SerialPort.readStringUntil('\n');
        command.trim();

        if (command.startsWith("SLIDER_"))
        {
            int newAngle = command.substring(7).toInt();
            newAngle = constrain(newAngle, 0, 180);

            if (newAngle != sliderAngle)
            {
                sliderAngle = newAngle;
                sliderServo1.write(sliderAngle);
                sliderServo2.write(180 - sliderAngle);
            }
        }
        else if (command.startsWith("JOY_SERVO_"))
        {
            int newAngle = command.substring(10).toInt();
            newAngle = constrain(newAngle, 0, 180);

            if (newAngle != joystickServoAngle)
            {
                joystickServoAngle = newAngle;
                joystickServo.write(joystickServoAngle);
            }
        }
    }

    // Send sensor data every 300ms
    if (millis() - lastSensorSend >= 300)
    {
        lastSensorSend = millis();

        String data = "SENSORS:";
        for (int i = 0; i < NUM_SENSORS; i++)
        {
            float dist = measureDistance(SENSOR_PINS[i][0], SENSOR_PINS[i][1]);
            data += String(dist, 1);
            if (i < NUM_SENSORS - 1)
                data += ",";
        }

        SerialPort.println(data); // Send via UART
    }

    delay(10);
}