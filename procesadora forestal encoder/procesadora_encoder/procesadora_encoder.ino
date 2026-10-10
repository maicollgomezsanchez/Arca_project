 const float OFFSET = 0.35;
const float CUENTAS_POR_M = (1024.0 * 4) / (PI * 0.145);

volatile long position = 0;
volatile int dir = 1;

void irA() {
  dir = (digitalRead(3) == HIGH) ? 1 : -1;
  position += dir;
}
void irB() {
  dir = (digitalRead(2) == HIGH) ? -1 : 1;
  position += dir;
}
void resetPos() {
  position = 0;  // ← reinicia al recibir pulso ALTO
}

void setup() {
  Serial.begin(115200);
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  pinMode(4, INPUT_PULLUP);  // ← pin de reset (D4)
  attachInterrupt(digitalPinToInterrupt(2), irA, RISING);
  attachInterrupt(digitalPinToInterrupt(3), irB, FALLING);
  attachInterrupt(digitalPinToInterrupt(4), resetPos, CHANGE);  // ← flanco ascendente
}

void loop() {
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 100) {
    float metros = ((float)position / CUENTAS_POR_M) + OFFSET;
    Serial.print("m: "); Serial.print(metros, 3);
    Serial.print("  dir: "); Serial.print(dir == 1 ? "→" : "←");
    Serial.println();
    lastPrint = millis();
  }
}   