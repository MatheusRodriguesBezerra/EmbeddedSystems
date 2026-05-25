#include "letter_leds.h"

static const uint8_t BINARY_LED_PINS[5] = {
    PIN_LED_L1,
    PIN_LED_L2,
    PIN_LED_L3,
    PIN_LED_L4,
    PIN_LED_L5,
};

static const uint8_t MODE_LED_PINS[3] = {
    PIN_LED_DECRYPT,
    PIN_LED_ENCRYPT,
    PIN_LED_MESSAGE,
};

void initAllLeds() {
  for (uint8_t i = 0; i < 3; i++) {
    pinMode(MODE_LED_PINS[i], OUTPUT);
    digitalWrite(MODE_LED_PINS[i], LED_OFF);
  }
  for (uint8_t i = 0; i < 5; i++) {
    pinMode(BINARY_LED_PINS[i], OUTPUT);
    digitalWrite(BINARY_LED_PINS[i], LED_OFF);
  }
}

void clearBinaryLeds() {
  setBinaryValue(0);
}

void setAllBinaryLeds(bool on) {
  uint8_t level = on ? LED_ON : LED_OFF;
  for (uint8_t i = 0; i < 5; i++) {
    digitalWrite(BINARY_LED_PINS[i], level);
  }
}

void setBinaryValue(uint8_t value) {
  value &= 0x1F;
  for (uint8_t i = 0; i < 5; i++) {
    digitalWrite(BINARY_LED_PINS[i], (value & (1 << i)) ? LED_ON : LED_OFF);
  }
}

uint8_t letterToBinaryValue(char letter) {
  if (letter >= 'a' && letter <= 'z') {
    letter = (char)(letter - 'a' + 'A');
  }
  if (letter < 'A' || letter > 'Z') {
    return 0;
  }
  return (uint8_t)(letter - 'A' + 1);
}

void showLetterOnBinaryLeds(char letter, uint16_t durationMs) {
  uint8_t value = letterToBinaryValue(letter);
  if (value == 0) {
    return;
  }

  Serial.print(F("LED bin "));
  Serial.print(letter);
  Serial.print(F(" val="));
  Serial.println(value);

  setBinaryValue(value);
  delay(durationMs);
  clearBinaryLeds();
}

static void blinkPinOnce(uint8_t pin, uint16_t ms) {
  digitalWrite(pin, LED_ON);
  delay(ms);
  digitalWrite(pin, LED_OFF);
}

void validateModeLeds() {
  Serial.println(F("--- Teste LEDs modo DEC/ENC/MSG ---"));
  initAllLeds();

  blinkPinOnce(PIN_LED_DECRYPT, 400);
  Serial.print(F("  DEC pino "));
  Serial.println(PIN_LED_DECRYPT);
  blinkPinOnce(PIN_LED_ENCRYPT, 400);
  Serial.print(F("  ENC pino "));
  Serial.println(PIN_LED_ENCRYPT);
  blinkPinOnce(PIN_LED_MESSAGE, 400);
  Serial.print(F("  MSG pino "));
  Serial.println(PIN_LED_MESSAGE);

  digitalWrite(PIN_LED_DECRYPT, LED_ON);
  delay(800);
  digitalWrite(PIN_LED_DECRYPT, LED_OFF);
  Serial.println(F("--- Fim teste LEDs modo ---"));
}

void selfTestBinaryLeds() {
  Serial.println(F("--- Teste L1-L5 ---"));

  const char samples[] = {'A', 'C', 'P'};
  for (uint8_t i = 0; i < 3; i++) {
    showLetterOnBinaryLeds(samples[i], 500);
  }

  Serial.println(F("  L5 isolado (letra P=16)"));
  setBinaryValue(16);
  delay(800);
  clearBinaryLeds();

  Serial.println(F("  Todos L1-L5 ON"));
  setAllBinaryLeds(true);
  delay(800);
  clearBinaryLeds();
  Serial.println(F("--- Fim teste L1-L5 ---"));
}

void playDecryptLetterSequence(const char *plain, uint16_t letterMs, uint16_t allOnMs) {
  if (plain == nullptr) {
    return;
  }

  for (uint8_t i = 0; plain[i] != '\0'; i++) {
    char c = plain[i];
    if (c < 'A' || c > 'Z') {
      continue;
    }
    showLetterOnBinaryLeds(c, letterMs);
  }

  clearBinaryLeds();
  setAllBinaryLeds(true);
  delay(allOnMs);
  clearBinaryLeds();
}
