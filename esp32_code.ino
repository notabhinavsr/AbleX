#include <Wire.h>
#include <MPU6050.h>
#include <ESP32Servo.h>

MPU6050 mpu;
Servo headServo;

float sensitivity = 0.4;
int deadZone = 1;

const int btn1Pin  = 4;    // Button 1: click / long-press STT / long-press cursor toggle
const int btn2Pin  = 5;    // Button 2: (unused)
const int servoPin = 18;   // Servo motor

// ── Mode ───────────────────────────────────────────────
bool servoMode = false;     // false = cursor, true = servo control

// ── Button 1 (click + long-press) ──────────────────────
bool lastBtn1State          = HIGH;
unsigned long btn1PressStart = 0;
bool btn1SttReady            = false;   // true once held ≥3s (STT fires on release)
bool btn1CursorToggleSent    = false;   // true once 7s toggle has fired

// ── Button 2 (unused) ──────────────────────────────────
bool lastBtn2State = HIGH;

// ── Servo smoothing ────────────────────────────────────
int currentServoAngle = 90; // start at neutral

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  pinMode(btn1Pin, INPUT_PULLUP);
  pinMode(btn2Pin, INPUT_PULLUP);

  headServo.setPeriodHertz(50);            // standard 50Hz servo
  headServo.attach(servoPin, 544, 2400);   // min/max pulse width in µs for 0-180°
  headServo.write(90);  // neutral position

  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("MPU6050 failed");
    while (1);
  }

  Serial.println("READY");
}

void loop() {

  // ===== READ SERIAL COMMANDS FROM PYTHON =====
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "SERVO_ON") {
      servoMode = true;
      Serial.println("ACK_SERVO_ON");
    } else if (cmd == "SERVO_OFF") {
      servoMode = false;
      headServo.write(90);  // return to neutral
      Serial.println("ACK_SERVO_OFF");
    }
  }

  // ===== GYRO READING =====
  int16_t gx, gy, gz;
  mpu.getRotation(&gx, &gy, &gz);

  float pitch = gx / 131.0;
  float yaw   = gz / 131.0;

  if (abs(pitch) < deadZone) pitch = 0;
  if (abs(yaw) < deadZone) yaw = 0;

  int dx = yaw * sensitivity;
  int dy = pitch * sensitivity;

  // Always send motion data so Python knows head position
  Serial.print("M,");
  Serial.print(dx);
  Serial.print(",");
  Serial.println(dy);

  // ===== SERVO MODE → continuous rotation servo =====
  // 90 = STOP, <90 = rotate one way, >90 = rotate other way
  if (servoMode) {
    if (abs(pitch) < 3) {
      // Head is neutral → stop the servo
      headServo.write(90);
    } else {
      // Map pitch to speed: ±30 deg/s → speed offset ±20 from 90
      int speed = 90 + constrain(map((int)pitch, -30, 30, -20, 20), -20, 20);
      headServo.write(speed);
    }
  }

  // ===== BUTTON 1 → CLICK / STT (3s+release) / CURSOR TOGGLE (7s) =====
  bool btn1State = digitalRead(btn1Pin);

  // Falling edge: button just pressed
  if (lastBtn1State == HIGH && btn1State == LOW) {
    btn1PressStart       = millis();
    btn1SttReady         = false;
    btn1CursorToggleSent = false;
  }

  // While held down, check durations
  if (btn1State == LOW && btn1PressStart > 0) {
    unsigned long held = millis() - btn1PressStart;

    // 7-second long-press → toggle cursor control (fires immediately)
    if (held >= 7000 && !btn1CursorToggleSent) {
      Serial.println("CURSOR_TOGGLE");
      btn1CursorToggleSent = true;
      btn1SttReady = false;  // cancel STT if held past 7s
    }
    // 3-second threshold reached → mark STT ready (fires on release)
    else if (held >= 3000 && !btn1SttReady) {
      btn1SttReady = true;
    }
  }

  // Rising edge: button released
  if (lastBtn1State == LOW && btn1State == HIGH) {
    // Debounce: wait 50ms and re-read
    delay(50);
    btn1State = digitalRead(btn1Pin);
    if (btn1State == HIGH) {
      if (btn1SttReady && !btn1CursorToggleSent) {
        // Held ≥3s but <7s, then released → trigger STT
        Serial.println("STT");
      } else if (!btn1SttReady && !btn1CursorToggleSent) {
        // Short press → click
        Serial.println("CLK");
      }
      btn1PressStart = 0;
    }
  }
  lastBtn1State = btn1State;

  // ===== BUTTON 2 (unused — reserved for future) =====
  bool btn2State = digitalRead(btn2Pin);
  lastBtn2State = btn2State;

  delay(5);
}

