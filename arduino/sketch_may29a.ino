// LED Pins
int ledPins[] = {13, 12, 11, 10};
bool ledStates[] = {false, false, false, false};

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 4; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }
  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    // Commands: 'A' = Yellow, 'B' = Green, 'C' = Blue, 'D' = White
    // Lowercase = OFF, Uppercase = ON
    if (cmd == 'A') { digitalWrite(ledPins[0], HIGH); Serial.println("YELLOW:ON"); }
    else if (cmd == 'a') { digitalWrite(ledPins[0], LOW);  Serial.println("YELLOW:OFF"); }
    else if (cmd == 'B') { digitalWrite(ledPins[1], HIGH); Serial.println("GREEN:ON"); }
    else if (cmd == 'b') { digitalWrite(ledPins[1], LOW);  Serial.println("GREEN:OFF"); }
    else if (cmd == 'C') { digitalWrite(ledPins[2], HIGH); Serial.println("BLUE:ON"); }
    else if (cmd == 'c') { digitalWrite(ledPins[2], LOW);  Serial.println("BLUE:OFF"); }
    else if (cmd == 'D') { digitalWrite(ledPins[3], HIGH); Serial.println("WHITE:ON"); }
    else if (cmd == 'd') { digitalWrite(ledPins[3], LOW);  Serial.println("WHITE:OFF"); }
  }
}
