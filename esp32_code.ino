#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

float sensitivity = 0.4;
int deadZone = 1;

const int btn1Pin = 4;    // Button 1: click / long-press STT / long-press cursor toggle
const int btn2Pin = 5;    // Button 2: (unused)

// ── Button 1 (click + long-press) ──────────────────────
bool lastBtn1State          = HIGH;
unsigned long btn1PressStart = 0;
bool btn1SttReady            = false;   // true once held ≥3s (STT fires on release)
bool btn1CursorToggleSent    = false;   // true once 7s toggle has fired

// ── Button 2 (unused) ──────────────────────────────────
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
  // btn2 read kept for potential future use
  bool btn2State = digitalRead(btn2Pin);
  lastBtn2State = btn2State;

  delay(5);
}
