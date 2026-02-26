#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

float sensitivity = 0.4;
int deadZone = 1;

const int btn1Pin = 4;    // Button 1: click (select/double/right)
const int btn2Pin = 5;    // Button 2: STT voice typing

// ── Button 1 (click) ───────────────────────────────────
bool lastBtn1State = HIGH;

// ── Button 2 (STT) ─────────────────────────────────────
bool lastBtn2State = HIGH;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  pinMode(btn1Pin, INPUT_PULLUP);
  pinMode(btn2Pin, INPUT_PULLUP);

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

  // ===== BUTTON 1 → CLICK (with debounce) =====
  bool btn1State = digitalRead(btn1Pin);

  if (lastBtn1State == LOW && btn1State == HIGH) {
    // Debounce: wait 50ms and re-read
    delay(50);
    btn1State = digitalRead(btn1Pin);
    if (btn1State == HIGH) {
      Serial.println("CLK");
    }
  }
  lastBtn1State = btn1State;

  // ===== BUTTON 2 → STT =====
  bool btn2State = digitalRead(btn2Pin);

  // Button pressed (falling edge) = trigger STT
  if (lastBtn2State == HIGH && btn2State == LOW) {
    Serial.println("STT");
  }
  lastBtn2State = btn2State;

  delay(5);
}
