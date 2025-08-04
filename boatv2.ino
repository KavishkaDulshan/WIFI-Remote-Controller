#include <ESP32Servo.h>

const int SLIDER_SERVO1_PIN = 18;
const int SLIDER_SERVO2_PIN = 19;
const int JOYSTICK_SERVO_PIN = 21;
const int NUM_SENSORS = 3;
const int MAX_DISTANCE = 200;

const int SENSOR_PINS[NUM_SENSORS][2] = {
    {25, 26}, {27, 14}, {12, 13}};

Servo sliderServo1;
Servo sliderServo2;
Servo joystickServo;

int sliderAngle = 90;
int joystickServoAngle = 90;
HardwareSerial SerialPi(1);
const int RXPIN = 16;
const int TXPIN = 17;
unsigned long lastSensorSend = 0;

void setup()
{
    Serial.begin(115200);
    for (int i = 0; i < NUM_SENSORS; i++)
    {
        pinMode(SENSOR_PINS[i][0], OUTPUT);
        pinMode(SENSOR_PINS[i][1], INPUT);
        digitalWrite(SENSOR_PINS[i][0], LOW);
    }

    SerialPi.begin(115200, SERIAL_8N1, RXPIN, TXPIN);
    sliderServo1.attach(SLIDER_SERVO1_PIN);
    sliderServo2.attach(SLIDER_SERVO2_PIN);
    joystickServo.attach(JOYSTICK_SERVO_PIN);

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
    return (distance <= 0 || distance > MAX_DISTANCE) ? -1.0 : distance;
}

void loop()
{
    if (SerialPi.available())
    {
        String command = SerialPi.readStringUntil('\n');
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
        SerialPi.println(data);
    }
    delay(10);
}