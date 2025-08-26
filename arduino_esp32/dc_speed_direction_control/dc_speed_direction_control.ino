#include <Wire.h>

// MPU6050 I2C address
#define MPU6050_ADDR 0x68

// MPU6050 register addresses
#define PWR_MGMT_1   0x6B
#define ACCEL_XOUT_H 0x3B
#define GYRO_XOUT_H  0x43

// IBT-2 Motor Driver pins
#define RPWM_PIN 25  // Right PWM (forward)
#define LPWM_PIN 26  // Left PWM (backward)
#define R_EN_PIN 27  // Right Enable
#define L_EN_PIN 14  // Left Enable

void setup() {
  Serial.begin(9600);
  Wire.begin();

  // Initialize MPU6050
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(PWR_MGMT_1);
  Wire.write(0); // Wake up the MPU6050
  Wire.endTransmission(true);

  // Initialize IBT-2 pins
  pinMode(RPWM_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);
  pinMode(R_EN_PIN, OUTPUT);
  pinMode(L_EN_PIN, OUTPUT);
  
  // Enable IBT-2
  digitalWrite(R_EN_PIN, HIGH);
  digitalWrite(L_EN_PIN, HIGH);

  Serial.println("MPU6050 and IBT-2 initialized");
}

// Function to print angle and motor status
void printAngleStatus(float angle, String motorStatus) {
  Serial.print("Angle Y: "); 
  Serial.print(angle);
  Serial.print(" degrees - ");
  Serial.println(motorStatus);
}

// Motor control functions
void motorForward(int speed, float angle) {
  analogWrite(RPWM_PIN, speed);  // PWM speed (0-255)
  analogWrite(LPWM_PIN, 0);      // Stop reverse
  printAngleStatus(angle, "Motor Forward");
}

void motorBackward(int speed, float angle) {
  analogWrite(RPWM_PIN, 0);      // Stop forward
  analogWrite(LPWM_PIN, speed);  // PWM speed (0-255)
  printAngleStatus(angle, "Motor Backward");
}

void motorStop(float angle) {
  analogWrite(RPWM_PIN, 0);
  analogWrite(LPWM_PIN, 0);
  printAngleStatus(angle, "Motor Stop");
  delay(500);
}

void loop() {
  int spd = 60;
  
  // Read accelerometer data
  int16_t accelX = readMPU6050(ACCEL_XOUT_H);
  int16_t accelY = readMPU6050(ACCEL_XOUT_H + 2);
  int16_t accelZ = readMPU6050(ACCEL_XOUT_H + 4);

  // Calculate tilt angle in degrees (horizontal axis)
  float angleY = atan2(-accelX, sqrt(accelY * accelY + accelZ * accelZ)) * 180.0 / PI;
  
  // Add 90 degrees to make 0 degrees horizontal
  angleY += 90;

  // Motor control based on angle
  if (angleY > 90) {
    motorForward(spd, angleY);
  } 
  else if (angleY < 85) {
    motorBackward(spd, angleY);
  } 
  else {
    // Angle between 85-90 degrees
    motorStop(angleY);
  }

  delay(100);
}

int16_t readMPU6050(uint8_t reg) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 2, true);

  int16_t value = Wire.read() << 8 | Wire.read();
  return value;
}
