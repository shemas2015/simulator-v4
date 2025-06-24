#define AC_IN_ZERO 27
#define TRIAC 26

#include <Wire.h>
#include <MPU6050.h>


unsigned int maxDimmer = 7250;
unsigned int minDimmer = 1000;
unsigned int dimmerValue = maxDimmer;
static bool setRotation = false;
int targetRoll = 0;
bool activo = false;
float roll;
bool haciaArriba = false;


hw_timer_t *timer = NULL;
MPU6050 mpu;



//---------------------- START POT FUNCITONS ----------------------
void IRAM_ATTR contarCruce() {
  timerWrite(timer, 0);  // Reinicia el contador
  timerAlarmWrite(timer, dimmerValue, false);
  timerAlarmEnable(timer);
}

void IRAM_ATTR dispararTRIAC() {
  digitalWrite(TRIAC, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIAC, LOW);
}
//---------------------- END POT FUNCITONS ----------------------

// ---------------------- START ARM LOCATION FUNCIOTNS ----------------------
void getAngle() {
  static unsigned long lastUpdate = 0;
  unsigned long now = millis();
  if (now - lastUpdate < 500) return;
  lastUpdate = now;

  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);

  float axg = ax / 16384.0;
  float ayg = ay / 16384.0;
  float azg = az / 16384.0;

  float pitch = atan2(ayg, sqrt(axg * axg + azg * azg)) * 180.0 / PI;
  roll  = atan2(-axg, azg) * 180.0 / PI;

  
}
// ---------------------- END ARM LOCATION FUNCIOTNS ----------------------

void setup() {
  Serial.begin(115200);
  pinMode(AC_IN_ZERO, INPUT);
  pinMode(TRIAC, OUTPUT);
  digitalWrite(TRIAC, LOW);

  // Delay freq interruption
  attachInterrupt(digitalPinToInterrupt(AC_IN_ZERO), contarCruce, FALLING);
  timer = timerBegin(0, 80, true);  // 80 prescaler → 1 µs por tick
  timerAttachInterrupt(timer, &dispararTRIAC, true);

  //Arm location config
  Wire.begin(32, 33);  // SDA , SCL 
  mpu.initialize();
  if (!mpu.testConnection()) {
    Serial.println("MPU6050 connection failed");
    while (1);
  }
}

void loop() {
  // Leer serial en formato "velocidad,ángulo"
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    int sep = input.indexOf(',');
    if (sep != -1) {
      int velocidad = input.substring(0, sep).toInt();
      int angulo = input.substring(sep + 1).toInt();

      if (velocidad >= 1 && velocidad <= 100) {
        dimmerValue = map(velocidad, 0, 100, maxDimmer, minDimmer);
        targetRoll = angulo;
        activo = true;
        setRotation = true;

        Serial.print("Set velocidad: "); Serial.print(velocidad);
        Serial.print(" → dimmerValue: "); Serial.print(dimmerValue);
        Serial.print(" | Objetivo roll: "); Serial.println(targetRoll);
      }
    }
  }

  
  
  if (activo) {
    getAngle();  // actualiza variable global 'roll'
    if (setRotation) {
      if (targetRoll < roll) {
        Serial.println("Abajo");
        haciaArriba = false;
      } else if (targetRoll > roll) {
        Serial.println("Arriba");
        haciaArriba = true;
      } else {
        Serial.println("Ya está en el ángulo objetivo");
      }
      setRotation = false;
    }
    
    bool objetivoAlcanzado = false;
    if (haciaArriba) {
      objetivoAlcanzado = roll >= targetRoll;
    } else {
      objetivoAlcanzado = roll <= targetRoll;
    }

    if (objetivoAlcanzado) {
      activo = false;
      dimmerValue = maxDimmer;
      Serial.println("Objetivo alcanzado. Actuador detenido.");
    }
  
  }

  
}
