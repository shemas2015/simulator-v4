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
int selectedMotor = -1;     // Motor selection: 0=left, 1=right, -1=not set
int manualSpeedPWM = 150;   // Speed for manual control during motor selection

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

  

  Serial.println("Potentiometer and IBT-2 initialized");
  Serial.println("Select motor: 0=left, 1=right");

  // Wait for valid motor selection (manual control also works here)
  unsigned long lastPrompt = 0;
  unsigned long lastManualCommandTime = 0;
  while (selectedMotor < 0) {
    if (Serial.available() > 0) {
      char firstChar = Serial.peek();

      // Check if it's a manual command
      if (firstChar == 'f' || firstChar == 'b') {
        char cmd = Serial.read();
        lastManualCommandTime = millis();  // Update timestamp
        if (cmd == 'f') {
          analogWrite(RPWM_PIN, manualSpeedPWM);
          analogWrite(LPWM_PIN, 0);
        } else if (cmd == 'b') {
          analogWrite(RPWM_PIN, 0);
          analogWrite(LPWM_PIN, manualSpeedPWM);
        }
        // Don't process further - continue waiting for motor selection
      }
      // Check if it's a digit (motor selection)
      else if (firstChar == '0' || firstChar == '1') {
        String input = Serial.readStringUntil('\n');
        input.trim();
        int motor = input.toInt();
        if (motor == 0 || motor == 1) {
          selectedMotor = motor;
          Serial.print("Motor ");
          Serial.print(selectedMotor == 0 ? "left" : "right");
          Serial.println(" selected");
        }
      }
      // Invalid input - consume and ignore
      else {
        Serial.read();
      }
    }

    // Stop motor if no manual command received within timeout (200ms)
    if (millis() - lastManualCommandTime > 50) {
      analogWrite(RPWM_PIN, 0);
      analogWrite(LPWM_PIN, 0);
    }

    if (millis() - lastPrompt > 2000) {
      Serial.println("Waiting for motor selection (0 left or 1 right)..."); //ATENTION!! add a led inficator to know the state (wating set mmotor)
      lastPrompt = millis();
    }
    delay(100);
  }


  // Create FreeRTOS task for potentiometer reading
  xTaskCreate(
    potentiometerTask,    // Task function
    "PotReader",          // Task name
    2048,                 // Stack size
    NULL,                 // Parameters
    1,                    // Priority
    NULL                  // Task handle
  );

  
}


void loop() {

  // Check for serial input only if not currently moving
  if (Serial.available() > 0 && !parametersSet) {
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
    positionMotor(inputSpeed);
  } else {
    // Keep motor stopped until parameters are set
    analogWrite(RPWM_PIN, 0);
    analogWrite(LPWM_PIN, 0);
  }

  delay(10);


}


// Safe motor control functions with direction tracking
void motorForward(int speed, float angle) {
  if (currentDirection == MOTOR_BACKWARD) {
    // Stop motor first if changing from backward to forward
    motorStop();
  }

  analogWrite(RPWM_PIN, speed);  // PWM speed (0-255)
  analogWrite(LPWM_PIN, 0);      // Stop reverse
  currentDirection = MOTOR_FORWARD;
}

void motorBackward(int speed, float angle) {
  if (currentDirection == MOTOR_FORWARD) {
    // Stop motor first if changing from forward to backward
    motorStop();
  }

  analogWrite(RPWM_PIN, 0);      // Stop forward
  analogWrite(LPWM_PIN, speed);  // PWM speed (0-255)
  currentDirection = MOTOR_BACKWARD;
}

void motorStop() {
  analogWrite(RPWM_PIN, 0);
  analogWrite(LPWM_PIN, 0);
  currentDirection = MOTOR_STOPPED;

  delay(50);//ATENTION!!! time to stop , to prevent damages!
}

// Function to position motor based on current and target angles
void positionMotor( int speed) {
  float angleDifference = currentAngle - targetAngle;

  if (abs(angleDifference) <= 5.0) {
    // Within ±5 degrees of target - stop motor
    motorStop();
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
  while (true) {
    
    // Read potentiometer value (0-4095) and convert to angle (0-180)
    int potValue = analogRead(POT_PIN);

    if(selectedMotor == 1){
      currentAngle = map(potValue, 0, 4095, 0, 180);
    }
    else if(selectedMotor == 0){
      currentAngle = map(potValue, 4095, 0, 0, 180);
    }

    /*
    //ATENTION!!! the print generate a delay fail, put thi only when need debug
    Serial.print("Current position: ");
    Serial.println(currentAngle);
    */
    
    vTaskDelay(30 / portTICK_PERIOD_MS); // 5ms delay for high-frequency reading
  }
}
