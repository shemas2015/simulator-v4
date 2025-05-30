unsigned int maxDimmer = 7250;
unsigned int minDimmer = 1000;
unsigned int dimmerValue = maxDimmer;
const int AC_IN_ZERO = 2;
const int TRIAC = 8;
volatile unsigned long deltaTime = 0;

int REL1 = 9;
int REL2 = 10;

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
  if (Serial.available()) {
    unsigned int val = Serial.parseInt();
    if (val < 100 and val > 0) {
      dimmerValue = map(val,0,100,maxDimmer,minDimmer);
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
