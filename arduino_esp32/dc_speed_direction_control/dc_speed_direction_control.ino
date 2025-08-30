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


// Global variables for serial input
int inputSpeed = 0;         // No default speed
float targetAngle = 0.0;    // No default target angle
bool parametersSet = false; // Flag to track if parameters have been set

// Motor direction tracking for safety
enum MotorDirection {
  MOTOR_STOPPED,
  MOTOR_FORWARD,
  MOTOR_BACKWARD
};

MotorDirection currentDirection = MOTOR_STOPPED;


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

  // Initialize motor in stopped state
  analogWrite(RPWM_PIN, 0);
  analogWrite(LPWM_PIN, 0);

  Serial.println("MPU6050 and IBT-2 initialized");
  Serial.println("Moving to initial position (85-95 degrees)...");

  // Initial positioning - move motor to between 85-95 degrees
  delay(1000); // Wait for MPU6050 to stabilize

  while (true) {
    // Read accelerometer data
    int16_t accelX = readMPU6050(ACCEL_XOUT_H);
    int16_t accelY = readMPU6050(ACCEL_XOUT_H + 2);
    int16_t accelZ = readMPU6050(ACCEL_XOUT_H + 4);

    // Calculate current angle
    float currentAngle = atan2(-accelX, sqrt(accelY * accelY + accelZ * accelZ)) * 180.0 / PI;
    currentAngle += 90;

    // Position motor to 90 degrees (center of 85-95 range)
    positionMotor(currentAngle, 90.0, 80); // Use moderate speed for initial positioning

    // Check if we're in the target range
    if (currentAngle >= 85.0 && currentAngle <= 95.0) {
      motorStop(currentAngle);
      Serial.println("Initial position reached!");
      break;
    }

    delay(100);
  }

  Serial.println("Motor stopped - waiting for input (format: speed,angle)");
}

// Function to print angle and motor status
void printAngleStatus(float angle, String motorStatus) {
  Serial.print("Angle Y: ");
  Serial.print(angle);
  Serial.print(" degrees - ");
  Serial.println(motorStatus);
}

// Safe motor control functions with direction tracking
void motorForward(int speed, float angle) {
  if (currentDirection == MOTOR_BACKWARD) {
    // Stop motor first if changing from backward to forward
    motorStop(angle);
  }

  analogWrite(RPWM_PIN, speed);  // PWM speed (0-255)
  analogWrite(LPWM_PIN, 0);      // Stop reverse
  currentDirection = MOTOR_FORWARD;
  //printAngleStatus(angle, "Motor Forward");
}

void motorBackward(int speed, float angle) {
  if (currentDirection == MOTOR_FORWARD) {
    // Stop motor first if changing from forward to backward
    motorStop(angle);
  }

  analogWrite(RPWM_PIN, 0);      // Stop forward
  analogWrite(LPWM_PIN, speed);  // PWM speed (0-255)
  currentDirection = MOTOR_BACKWARD;
  //printAngleStatus(angle, "Motor Backward");
}

void motorStop(float angle) {
  analogWrite(RPWM_PIN, 0);
  analogWrite(LPWM_PIN, 0);
  currentDirection = MOTOR_STOPPED;
  printAngleStatus(angle, "Motor Stop");
  //delay(500);
  delay(500);//ATENTION!!! time to stop , to prevent damages!
}

// Function to position motor based on current and target angles
void positionMotor(float currentAngle, float targetAngle, int speed) {
  float angleDifference = currentAngle - targetAngle;

  if (abs(angleDifference) <= 10.0) {
    // Within ±5 degrees of target - stop motor
    motorStop(currentAngle);
    parametersSet = false;
  }
  else if (currentAngle > targetAngle) {
    // Current angle is greater than target - move forward
    motorForward(speed, currentAngle);
  }
  else {
    // Current angle is less than target - move backward
    motorBackward(speed, currentAngle);
  }
}



void loop() {
  // Check for serial input
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    // Parse input format: "speed,angle" (e.g., "100,45")
    int commaIndex = input.indexOf(',');
    if (commaIndex > 0) {
      inputSpeed = input.substring(0, commaIndex).toInt();
      targetAngle = input.substring(commaIndex + 1).toFloat();
      parametersSet = true; // Mark that parameters have been set

      Serial.print("New settings - Speed: ");
      Serial.print(inputSpeed);
      Serial.print(", Target Angle: ");
      Serial.println(targetAngle);
    }
  }

  // Read accelerometer data
  int16_t accelX = readMPU6050(ACCEL_XOUT_H);
  int16_t accelY = readMPU6050(ACCEL_XOUT_H + 2);
  int16_t accelZ = readMPU6050(ACCEL_XOUT_H + 4);

  // Calculate tilt angle in degrees (horizontal axis)
  float currentAngle = atan2(-accelX, sqrt(accelY * accelY + accelZ * accelZ)) * 180.0 / PI;

  // Add 90 degrees to make 0 degrees horizontal
  currentAngle += 90;

  // Print current angle on each reading
  Serial.print("Current Angle: ");
  Serial.println(currentAngle);

  // Only move motor if parameters have been set via serial input
  if (parametersSet) {
    positionMotor(currentAngle, targetAngle, inputSpeed);
  } else {
    // Keep motor stopped until parameters are set
    analogWrite(RPWM_PIN, 0);
    analogWrite(LPWM_PIN, 0);
  }

  delay(10);

}

int16_t readMPU6050(uint8_t reg) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR, 2, true);

  int16_t value = Wire.read() << 8 | Wire.read();
  return value;
}
