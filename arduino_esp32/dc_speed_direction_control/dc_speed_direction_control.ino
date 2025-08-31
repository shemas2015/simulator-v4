// Potentiometer pin
#define POT_PIN 34

// IBT-2 Motor Driver pins
#define RPWM_PIN 25  // Right PWM (forward)
#define LPWM_PIN 26  // Left PWM (backward)
#define R_EN_PIN 27  // Right Enable
#define L_EN_PIN 14  // Left Enable


// Global variables for serial input
int inputSpeed = 0;         // No default speed
float targetAngle = 0.0;    // No default target angle
bool parametersSet = false; // Flag to track if parameters have been set

// Global variables for potentiometer reading (shared between tasks)
volatile float currentAngle = 0.0;

// Timing variable for periodic printing
unsigned long lastPrintTime = 0;


// Motor direction tracking for safety
enum MotorDirection {
  MOTOR_STOPPED,
  MOTOR_FORWARD,
  MOTOR_BACKWARD
};

MotorDirection currentDirection = MOTOR_STOPPED;


void setup() {
  Serial.begin(9600);

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

  Serial.println("Potentiometer and IBT-2 initialized");
  Serial.println("Moving to initial position (85-95 degrees)...");

  // Initial positioning - move motor to 90 degrees
  delay(1000); // Wait for system to stabilize

  // Create FreeRTOS task for potentiometer reading
  xTaskCreate(
    potentiometerTask,    // Task function
    "PotReader",          // Task name
    2048,                 // Stack size
    NULL,                 // Parameters
    1,                    // Priority
    NULL                  // Task handle
  );

  
  targetAngle = 90;
  while (true) {
    // Read potentiometer value (0-4095) and convert to angle (0-180)
    int potValue = analogRead(POT_PIN);
    //float currentAngle = map(potValue, 0, 4095, 0, 180);

    // Position motor to 90 degrees (center of 85-95 range)
    positionMotor( 80); // Use moderate speed for initial positioning

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

  // Only move motor if we have valid potentiometer reading and parameters are set
  if (parametersSet) {
    positionMotor( inputSpeed);
  } else {
    // Keep motor stopped until parameters are set
    analogWrite(RPWM_PIN, 0);
    analogWrite(LPWM_PIN, 0);
  }
  
  
  // Print current position every second
  unsigned long currentTime = millis();
  if (currentTime - lastPrintTime >= 300) {
    Serial.print("Current Position: ");
    Serial.print(currentAngle);
    Serial.println(" degrees");
    lastPrintTime = currentTime;
  }
  

  delay(10);
  

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

  delay(500);//ATENTION!!! time to stop , to prevent damages!
}

// Function to position motor based on current and target angles
void positionMotor( int speed) {
  float angleDifference = currentAngle - targetAngle;

  if (abs(angleDifference) <= 5.0) {
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

// FreeRTOS task for continuous potentiometer reading
void potentiometerTask(void *parameter) {
  volatile float currentAngleTmp = 0.0;
  while (true) {
    // Get current time in milliseconds
    unsigned long readTime = millis();
    
    // Read potentiometer value (0-4095) and convert to angle (0-180)
    int potValue = analogRead(POT_PIN);
    currentAngleTmp = map(potValue, 0, 4095, 0, 180);
    
    if (currentAngleTmp  == 0) {
      // Invalid reading, don't update
      
    } else {
      currentAngle = currentAngleTmp;
      /*
      Serial.print("Time: ");
      Serial.print(readTime);
      Serial.print("ms - Current Angle: ");
      Serial.println(currentAngle);
      */
    }
    
    vTaskDelay(30 / portTICK_PERIOD_MS); // 5ms delay for high-frequency reading
  }
}
