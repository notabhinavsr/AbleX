#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

float sensitivity = 0.4;
int deadZone = 1;

const int switchPin = 4;

// ── Click detection ────────────────────────────────────
bool lastBtnState = HIGH;
unsigned long pressStartTime = 0;
bool pressed = false;

const unsigned long LONG_PRESS_MS = 600;  // hold > 600ms = right click

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  pinMode(switchPin, INPUT_PULLUP);

  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("MPU6050 failed");
    while (1);
  }

  Serial.println("READY");
}

void loop() {

  // ===== GYRO → CURSOR =====
  int16_t gx, gy, gz;
  mpu.getRotation(&gx, &gy, &gz);

  float pitch = gx / 131.0;
  float yaw   = gz / 131.0;

  if (abs(pitch) < deadZone) pitch = 0;
  if (abs(yaw) < deadZone) yaw = 0;

  int dx = yaw * sensitivity;
  int dy = pitch * sensitivity;

  Serial.print("M,");
  Serial.print(dx);
  Serial.print(",");
  Serial.println(dy);

  // ===== BUTTON → CLICK EVENTS =====
  bool currentState = digitalRead(switchPin);

  // Button pressed (falling edge: HIGH → LOW)
  if (lastBtnState == HIGH && currentState == LOW) {
    pressStartTime = millis();
    pressed = true;
  }

  // Button released (rising edge: LOW → HIGH)
  if (lastBtnState == LOW && currentState == HIGH && pressed) {
    unsigned long holdTime = millis() - pressStartTime;
    pressed = false;

    if (holdTime >= LONG_PRESS_MS) {
      Serial.println("RC");    // Long press → Right click
    } else {
      Serial.println("CLK");   // Short press → Python counts for single/double/triple
    }
  }

  lastBtnState = currentState;

  delay(5);
}
