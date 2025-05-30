unsigned int maxDimmer = 7250;
unsigned int minDimmer = 1000;
unsigned int dimmerValue = maxDimmer;
const int AC_IN_ZERO = 2;
const int TRIAC = 10;
volatile unsigned long deltaTime = 0;

int REL1 = 11;
int REL2 = 12;

void setup() {
  Serial.begin(9600);  // Iniciar comunicación serie
  pinMode(AC_IN_ZERO, INPUT);
  pinMode(TRIAC, OUTPUT);  // Establecer el pin TRIAC como salida
  digitalWrite(TRIAC, HIGH);
  attachInterrupt(digitalPinToInterrupt(AC_IN_ZERO), contarCruce, FALLING);

  //reles
  pinMode(REL1, OUTPUT);
  pinMode(REL2, OUTPUT);

  digitalWrite(REL1, LOW);
  digitalWrite(REL2, LOW);
}

void loop() {
  // Verifica si hay datos disponibles
  if (Serial.available()) {
    // Leer dirección (1 o 2)
    int direction = Serial.parseInt();

    if (direction == 1 || direction == 2) {
      // Aquí defines el sentido de giro con base en la dirección recibida
      // Por ejemplo: digitalWrite(DIR_PIN, direction);
      Serial.print("Dirección recibida: ");
      Serial.println(direction);
      if (direction == 1) {
        digitalWrite(REL1, LOW);
        digitalWrite(REL2, LOW);
      } else if(direction == 2) {
        digitalWrite(REL1, HIGH);
        digitalWrite(REL2, HIGH);
      }

      // Esperar al segundo valor (velocidad)
      while (!Serial.available());

      unsigned int val = Serial.parseInt();
      if (val < 100 && val > 0) {
        dimmerValue = map(val, 0, 100, maxDimmer, minDimmer);
        Serial.print("Velocidad recibida: ");
        Serial.println(val);
      }
    } else {
      Serial.println("Dirección inválida. Debe ser 1 o 2.");
    }
  }
}

void contarCruce() {
  delayMicroseconds(dimmerValue);
  digitalWrite(TRIAC, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIAC, LOW);
  static unsigned long lastPrint = 0;
}
