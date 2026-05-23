/*
 * Enigma Machine - Arduino Mega 2560
 * Ver COMPORTAMENTO.md e README.md
 *
 * Bibliotecas (Arduino Library Manager):
 *   - Keypad by Mark Stanley, Chris Young
 *   - LiquidCrystal I2C by Frank de Brabander
 */

#include <Wire.h>
#include <Keypad.h>
#include <LiquidCrystal_I2C.h>

#include "config.h"
#include "enigma.h"

enum UiMode { MODE_DECRYPT, MODE_ENCRYPT };

// Keypad 1: pinos 22-29
const byte KP1_ROWS = 4;
const byte KP1_COLS = 4;
char keys1[KP1_ROWS][KP1_COLS] = {
    {'A', 'B', 'C', 'D'},
    {'E', 'F', 'G', 'H'},
    {'I', 'J', 'K', 'L'},
    {'M', 'N', 'O', 'P'},
};
byte rowPins1[KP1_ROWS] = {22, 23, 24, 25};
byte colPins1[KP1_COLS] = {26, 27, 28, 29};
Keypad keypad1 = Keypad(makeKeymap(keys1), rowPins1, colPins1, KP1_ROWS, KP1_COLS);

// Keypad 2: pinos 30-37
const byte KP2_ROWS = 4;
const byte KP2_COLS = 4;
char keys2[KP2_ROWS][KP2_COLS] = {
    {'Q', 'R', 'S', 'T'},
    {'U', 'V', 'W', 'X'},
    {'Y', 'Z', KEY_SEND, KEY_MODE},
    {KEY_R1, KEY_R2, KEY_R3, KEY_RESET_SYNC},
};
byte rowPins2[KP2_ROWS] = {30, 31, 32, 33};
byte colPins2[KP2_COLS] = {34, 35, 36, 37};
Keypad keypad2 = Keypad(makeKeymap(keys2), rowPins2, colPins2, KP2_ROWS, KP2_COLS);

LiquidCrystal_I2C lcd(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);

UiMode uiMode = MODE_DECRYPT;
EnigmaConfig machineConfig;
String plainCompose = "";
String line1Cipher = "";
String line2Plain = "";
uint8_t compositionStart[3] = {0, 0, 0};

char serialLine[64];
uint8_t serialLineLen = 0;

unsigned long syncDeadline = 0;
bool awaitingSyncResponse = false;
bool lcdReady = false;

void scanI2CBus() {
  Serial.println(F("--- Scan I2C (SDA=20, SCL=21) ---"));
  byte found = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print(F("  Dispositivo em 0x"));
      if (addr < 16) Serial.print('0');
      Serial.println(addr, HEX);
      found++;
    }
  }
  if (found == 0) {
    Serial.println(F("  NENHUM dispositivo! Verifique 5V, GND, SDA, SCL e contraste."));
  } else {
    Serial.print(F("  Endereco em config.h: 0x"));
    Serial.println(LCD_I2C_ADDR, HEX);
    Serial.println(F("  Se LCD vazio, tente 0x27 ou 0x3F conforme o scan acima."));
  }
  Serial.println(F("--------------------------------"));
}

void blinkLed(uint8_t pin, uint16_t ms) {
  digitalWrite(pin, HIGH);
  delay(ms);
  digitalWrite(pin, LOW);
  delay(ms);
}

void debugKeyPress(char keypadId, char key) {
#if DEBUG_KEYS
  Serial.print(F("Keypad "));
  Serial.print(keypadId);
  Serial.print(F(" tecla=0x"));
  Serial.println((uint8_t)key, HEX);

  char buf[21];
  if (key >= 0x20 && key <= 0x7E) {
    snprintf(buf, sizeof(buf), "Tecla: %c (%c)", key, keypadId);
  } else {
    snprintf(buf, sizeof(buf), "Tecla: 0x%02X", (uint8_t)key);
  }
  printLcdLine(2, buf);
#endif
}

void setLeds(bool decryptOn, bool encryptOn, bool messageOn) {
  digitalWrite(PIN_LED_DECRYPT, decryptOn ? LED_ON : LED_OFF);
  digitalWrite(PIN_LED_ENCRYPT, encryptOn ? LED_ON : LED_OFF);
  digitalWrite(PIN_LED_MESSAGE, messageOn ? LED_ON : LED_OFF);

  Serial.print(F("LEDs DEC(48)="));
  Serial.print(decryptOn ? F("ON") : F("off"));
  Serial.print(F(" ENC(50)="));
  Serial.print(encryptOn ? F("ON") : F("off"));
  Serial.print(F(" MSG(52)="));
  Serial.println(messageOn ? F("ON") : F("off"));
}

void printLcdLine(uint8_t row, const String &text) {
#if LCD_MIRROR_SERIAL
  Serial.print(F("LCD["));
  Serial.print(row);
  Serial.print(F("]: "));
  Serial.println(text);
#endif
  if (!lcdReady) return;

  lcd.setCursor(0, row);
  lcd.print("                    ");
  lcd.setCursor(0, row);
  String clipped = text;
  if (clipped.length() > LCD_COLS) {
    clipped = clipped.substring(0, LCD_COLS);
  }
  lcd.print(clipped);
}

void updateRotorLine() {
  char buf[24];
  snprintf(buf, sizeof(buf), "R1:%u R2:%u R3:%u",
           machineConfig.positions[0],
           machineConfig.positions[1],
           machineConfig.positions[2]);
  printLcdLine(3, buf);
}

void clearMessageLines() {
  line1Cipher = "";
  line2Plain = "";
  printLcdLine(0, "");
  printLcdLine(1, "");
}

void snapshotCompositionStart() {
  compositionStart[0] = machineConfig.positions[0];
  compositionStart[1] = machineConfig.positions[1];
  compositionStart[2] = machineConfig.positions[2];
}

void refreshEncryptDisplay() {
  if (plainCompose.length() == 0) {
    clearMessageLines();
    return;
  }

  EnigmaConfig work = machineConfig;
  work.positions[0] = compositionStart[0];
  work.positions[1] = compositionStart[1];
  work.positions[2] = compositionStart[2];

  String cipher = enigmaProcessMessage(plainCompose, work);
  machineConfig.positions[0] = work.positions[0];
  machineConfig.positions[1] = work.positions[1];
  machineConfig.positions[2] = work.positions[2];

  line2Plain = plainCompose;
  line1Cipher = cipher;
  printLcdLine(0, line1Cipher);
  printLcdLine(1, line2Plain);
  updateRotorLine();
}

void applyDecryptPayload(const String &payload) {
  String clean = "";
  for (unsigned int i = 0; i < payload.length(); i++) {
    char c = toupper(payload.charAt(i));
    if (c >= 'A' && c <= 'Z') clean += c;
  }
  if (clean.length() == 0) return;

  EnigmaConfig work = machineConfig;
  String plain = enigmaProcessMessage(clean, work);
  machineConfig.positions[0] = work.positions[0];
  machineConfig.positions[1] = work.positions[1];
  machineConfig.positions[2] = work.positions[2];

  line1Cipher = clean;
  line2Plain = plain;
  printLcdLine(0, line1Cipher);
  printLcdLine(1, line2Plain);
  updateRotorLine();
  setLeds(false, false, true);
}

void enterDecryptMode() {
  uiMode = MODE_DECRYPT;
  plainCompose = "";
  clearMessageLines();
  printLcdLine(2, "");
  updateRotorLine();
  setLeds(true, false, false);
  Serial.println(F("MODE:DEC"));
}

void enterEncryptMode() {
  uiMode = MODE_ENCRYPT;
  plainCompose = "";
  clearMessageLines();
  printLcdLine(2, "");
  updateRotorLine();
  setLeds(false, true, false);
  Serial.println(F("MODE:ENC"));
}

void incrementRotor(uint8_t index) {
  machineConfig.positions[index] = (machineConfig.positions[index] + 1) % 26;
  updateRotorLine();
  if (uiMode == MODE_ENCRYPT && plainCompose.length() > 0) {
    snapshotCompositionStart();
    refreshEncryptDisplay();
  }
}

bool parsePosLine(const String &line) {
  int p = line.indexOf("POS:");
  if (p < 0) return false;

  int r1 = 0, r2 = 0, r3 = 0;
  int start = p + 4;
  String rest = line.substring(start);
  rest.trim();

  int c1 = rest.indexOf(',');
  if (c1 < 0) return false;
  int c2 = rest.indexOf(',', c1 + 1);
  if (c2 < 0) return false;

  r1 = rest.substring(0, c1).toInt();
  r2 = rest.substring(c1 + 1, c2).toInt();
  r3 = rest.substring(c2 + 1).toInt();

  machineConfig.positions[0] = constrain(r1, 0, 25);
  machineConfig.positions[1] = constrain(r2, 0, 25);
  machineConfig.positions[2] = constrain(r3, 0, 25);
  updateRotorLine();
  return true;
}

void resetRotorsToZero() {
  machineConfig.positions[0] = 0;
  machineConfig.positions[1] = 0;
  machineConfig.positions[2] = 0;
  updateRotorLine();
}

void requestSync() {
  Serial.println(F("SYNC"));
  awaitingSyncResponse = true;
  syncDeadline = millis() + SYNC_TIMEOUT_MS;
}

void finishSync(bool gotPos) {
  awaitingSyncResponse = false;
  if (!gotPos) {
    resetRotorsToZero();
    printLcdLine(2, "SYNC: sem resposta");
  } else {
    printLcdLine(2, "SYNC: OK");
  }
  delay(800);
  printLcdLine(2, "");
}

void handleResetSync() {
  if (uiMode == MODE_ENCRYPT) {
    plainCompose = "";
    clearMessageLines();
    setLeds(false, true, false);
  } else {
    clearMessageLines();
    setLeds(true, false, false);
  }
  requestSync();
}

void handleSend() {
  if (uiMode != MODE_ENCRYPT || plainCompose.length() == 0) return;

  refreshEncryptDisplay();
  Serial.print(F("SEND:"));
  Serial.println(line1Cipher);
  setLeds(false, true, true);
}

void handleSerialLine(const String &line) {
  if (line.startsWith(F("POS:"))) {
    if (parsePosLine(line)) {
      finishSync(true);
    }
    return;
  }

  if (line.startsWith(F("IN:"))) {
    if (uiMode == MODE_DECRYPT) {
      applyDecryptPayload(line.substring(3));
    }
    return;
  }

  if (line.startsWith(F("ACK:"))) {
    printLcdLine(2, line.substring(0, min((int)line.length(), LCD_COLS)));
    delay(500);
    printLcdLine(2, "");
    return;
  }

  if (line.startsWith(F("ERR:"))) {
    printLcdLine(2, line.substring(0, min((int)line.length(), LCD_COLS)));
    delay(1000);
    printLcdLine(2, "");
  }
}

void pollSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialLineLen > 0) {
        serialLine[serialLineLen] = '\0';
        handleSerialLine(String(serialLine));
        serialLineLen = 0;
      }
      continue;
    }
    if (serialLineLen < sizeof(serialLine) - 1) {
      serialLine[serialLineLen++] = c;
    }
  }

  if (awaitingSyncResponse && millis() > syncDeadline) {
    finishSync(false);
  }
}

bool isLetter(char key) {
  return (key >= 'A' && key <= 'Z') || (key >= 'a' && key <= 'z');
}

void handleKey(char key) {
  if (key == KEY_MODE) {
    if (uiMode == MODE_DECRYPT) {
      enterEncryptMode();
    } else {
      enterDecryptMode();
    }
    return;
  }

  if (key == KEY_RESET_SYNC) {
    handleResetSync();
    return;
  }

  if (uiMode == MODE_DECRYPT) {
    if (key == KEY_R1) incrementRotor(0);
    else if (key == KEY_R2) incrementRotor(1);
    else if (key == KEY_R3) incrementRotor(2);
    else if (isLetter(key)) {
      printLcdLine(2, "DEC: letras inativas");
    }
    return;
  }

  // MODE_ENCRYPT
  if (key == KEY_SEND) {
    handleSend();
    return;
  }
  if (key == KEY_R1) incrementRotor(0);
  else if (key == KEY_R2) incrementRotor(1);
  else if (key == KEY_R3) incrementRotor(2);
  else if (isLetter(key)) {
    if (plainCompose.length() < MAX_PLAIN_LEN) {
      if (plainCompose.length() == 0) {
        snapshotCompositionStart();
      }
      plainCompose += (char)toupper(key);
      refreshEncryptDisplay();
    }
  }
}

void setup() {
  pinMode(PIN_LED_DECRYPT, OUTPUT);
  pinMode(PIN_LED_ENCRYPT, OUTPUT);
  pinMode(PIN_LED_MESSAGE, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  setLeds(false, false, false);

  // LEDs ANTES do LCD: se I2C falhar, ainda vemos sinal de vida
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    blinkLed(PIN_LED_DECRYPT, 150);
    blinkLed(PIN_LED_ENCRYPT, 150);
    blinkLed(PIN_LED_MESSAGE, 150);
    digitalWrite(LED_BUILTIN, LOW);
    delay(150);
  }

  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println(F("ENIGMA: boot"));
  Serial.println(F("Se ve isto, o sketch esta a correr."));

  enigmaSetDefaultOrder(machineConfig);
  machineConfig.positions[0] = 0;
  machineConfig.positions[1] = 0;
  machineConfig.positions[2] = 0;

  Wire.begin();
  delay(100);
  scanI2CBus();

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcdReady = true;

  printLcdLine(0, "Enigma iniciado");
  updateRotorLine();
  Serial.println(F("LCD init() concluido"));

  enterDecryptMode();
  printLcdLine(2, "Aguardando IN:...");
  Serial.println(F("ENIGMA: pronto (modo DEC)"));
}

void loop() {
  pollSerial();

  char key1 = keypad1.getKey();
  if (key1 != NO_KEY) {
    debugKeyPress('1', key1);
    handleKey(key1);
  }

  char key2 = keypad2.getKey();
  if (key2 != NO_KEY) {
    debugKeyPress('2', key2);
    handleKey(key2);
  }
}
