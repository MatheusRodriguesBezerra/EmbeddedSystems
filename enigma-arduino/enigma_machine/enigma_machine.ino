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
#include "letter_leds.h"
#include "rotor_bank.h"

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
    {'Y', 'Z', KEY_NONE, KEY_NONE},
    {KEY_MODE, KEY_RESET, KEY_SYNC, KEY_SEND},
};
byte rowPins2[KP2_ROWS] = {30, 31, 32, 33};
byte colPins2[KP2_COLS] = {34, 35, 36, 37};
Keypad keypad2 = Keypad(makeKeymap(keys2), rowPins2, colPins2, KP2_ROWS, KP2_COLS);

// Keypad 3: pinos 38-45
const byte KP3_ROWS = 4;
const byte KP3_COLS = 4;
char keys3[KP3_ROWS][KP3_COLS] = {
    {KEY_R1_PLUS, KEY_R1, KEY_R2_PLUS, KEY_R2},
    {KEY_R3_PLUS, KEY_R3, KEY_R4_PLUS, KEY_R4},
    {KEY_R5_PLUS, KEY_R5, KEY_R6_PLUS, KEY_R6},
    {KEY_S1, KEY_S2, KEY_S3, KEY_S4},
};
byte rowPins3[KP3_ROWS] = {38, 39, 40, 41};
byte colPins3[KP3_COLS] = {42, 43, 44, 45};
Keypad keypad3 = Keypad(makeKeymap(keys3), rowPins3, colPins3, KP3_ROWS, KP3_COLS);

LiquidCrystal_I2C lcd(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);

UiMode uiMode = MODE_DECRYPT;
EnigmaConfig machineConfig;
String plainCompose = "";
String line1Cipher = "";
String line2Plain = "";
uint8_t compositionStartPos[MAX_ACTIVE_ROTORS] = {0, 0, 0, 0};
uint8_t compositionStartCount = 0;

char serialLine[96];
uint8_t serialLineLen = 0;

unsigned long syncDeadline = 0;
bool awaitingSyncResponse = false;
bool lcdReady = false;
bool messageActive = false;

void setLeds(bool decryptOn, bool encryptOn, bool messageOn);

bool hasDisplayedMessage() {
  return messageActive;
}

void refreshModeLeds() {
  bool decryptOn = (uiMode == MODE_DECRYPT);
  bool encryptOn = (uiMode == MODE_ENCRYPT);
  bool messageOn = hasDisplayedMessage();
  setLeds(decryptOn, encryptOn, messageOn);
}

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
  pinMode(PIN_LED_DECRYPT, OUTPUT);
  pinMode(PIN_LED_ENCRYPT, OUTPUT);
  pinMode(PIN_LED_MESSAGE, OUTPUT);

  digitalWrite(PIN_LED_DECRYPT, decryptOn ? LED_ON : LED_OFF);
  digitalWrite(PIN_LED_ENCRYPT, encryptOn ? LED_ON : LED_OFF);
  digitalWrite(PIN_LED_MESSAGE, messageOn ? LED_ON : LED_OFF);

  Serial.print(F("LEDs DEC("));
  Serial.print(PIN_LED_DECRYPT);
  Serial.print(decryptOn ? F(")=ON") : F(")=off"));
  Serial.print(F(" ENC("));
  Serial.print(PIN_LED_ENCRYPT);
  Serial.print(encryptOn ? F(")=ON") : F(")=off"));
  Serial.print(F(" MSG("));
  Serial.print(PIN_LED_MESSAGE);
  Serial.print(messageOn ? F(")=ON") : F(")=off"));
  Serial.println();
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
  rotorFormatLine(machineConfig, buf, sizeof(buf));
  printLcdLine(3, buf);
}

void clearMessageLines() {
  line1Cipher = "";
  line2Plain = "";
  messageActive = false;
  printLcdLine(0, "");
  printLcdLine(1, "");
  refreshModeLeds();
}

void snapshotCompositionStart() {
  compositionStartCount = machineConfig.slotCount;
  for (uint8_t i = 0; i < MAX_ACTIVE_ROTORS; i++) {
    compositionStartPos[i] = (i < compositionStartCount) ? machineConfig.slotPos[i] : 0;
  }
}

void refreshEncryptDisplay() {
  if (plainCompose.length() == 0) {
    clearMessageLines();
    return;
  }

  if (machineConfig.slotCount == 0) {
    printLcdLine(2, "Sem rotores");
    return;
  }

  EnigmaConfig work = machineConfig;
  work.slotCount = compositionStartCount;
  for (uint8_t i = 0; i < compositionStartCount; i++) {
    work.slotPos[i] = compositionStartPos[i];
  }

  String cipher = enigmaProcessMessage(plainCompose, work);
  for (uint8_t i = 0; i < compositionStartCount; i++) {
    machineConfig.slotPos[i] = work.slotPos[i];
  }

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

  if (machineConfig.slotCount == 0) {
    printLcdLine(2, "Sem rotores");
    return;
  }

  EnigmaConfig work = machineConfig;
  String plain = enigmaProcessMessage(clean, work);
  for (uint8_t i = 0; i < work.slotCount; i++) {
    machineConfig.slotPos[i] = work.slotPos[i];
  }

  line1Cipher = clean;
  line2Plain = plain;
  printLcdLine(0, line1Cipher);
  printLcdLine(1, line2Plain);
  updateRotorLine();
  messageActive = true;
  refreshModeLeds();

  playDecryptLetterSequence(line2Plain.c_str(), BINARY_LED_DISPLAY_MS, DECRYPT_FINISH_ALL_MS);
  refreshModeLeds();
}

void enterDecryptMode() {
  uiMode = MODE_DECRYPT;
  plainCompose = "";
  clearMessageLines();
  printLcdLine(2, "");
  updateRotorLine();
  refreshModeLeds();
  Serial.println(F("MODE:DEC"));
}

void enterEncryptMode() {
  uiMode = MODE_ENCRYPT;
  plainCompose = "";
  clearMessageLines();
  printLcdLine(2, "");
  updateRotorLine();
  refreshModeLeds();
  Serial.println(F("MODE:ENC"));
}

void requestSync() {
  Serial.println(F("SYNC"));
  awaitingSyncResponse = true;
  syncDeadline = millis() + SYNC_TIMEOUT_MS;
}

void finishSync(bool gotCfg) {
  awaitingSyncResponse = false;
  if (!gotCfg) {
    rotorClearAll(machineConfig);
    updateRotorLine();
    printLcdLine(2, "SYNC: sem resposta");
  } else {
    printLcdLine(2, "SYNC: OK");
  }
  delay(800);
  printLcdLine(2, "");
}

void handleReset() {
  if (uiMode == MODE_ENCRYPT) {
    plainCompose = "";
    clearMessageLines();
  } else {
    clearMessageLines();
  }
  rotorClearAll(machineConfig);
  updateRotorLine();
  refreshModeLeds();
}

void handleSync() {
  requestSync();
}

void handleSend() {
  if (uiMode != MODE_ENCRYPT || plainCompose.length() == 0) return;
  if (machineConfig.slotCount == 0) {
    printLcdLine(2, "Sem rotores");
    return;
  }

  refreshEncryptDisplay();
  char slotsBuf[48];
  rotorFormatSlotsCsv(machineConfig, slotsBuf, sizeof(slotsBuf));
  Serial.print(F("SEND:"));
  Serial.print(line1Cipher);
  Serial.print('|');
  Serial.println(slotsBuf);
  messageActive = true;
  refreshModeLeds();
}

void handleSerialLine(const String &line) {
  if (line.startsWith(F("CFG:"))) {
    if (rotorApplyCfgLine(machineConfig, line)) {
      updateRotorLine();
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

bool handleRotorKey(char key) {
  if (key >= KEY_R1_PLUS && key <= KEY_R6_PLUS) {
    uint8_t rotorId = (uint8_t)((key - KEY_R1_PLUS) / 2 + 1);
    rotorIncrementPending(machineConfig, rotorId);
    updateRotorLine();
    if (uiMode == MODE_ENCRYPT && plainCompose.length() > 0) {
      snapshotCompositionStart();
      refreshEncryptDisplay();
    }
    return true;
  }

  if (key >= KEY_R1 && key <= KEY_R6) {
    uint8_t rotorId = (uint8_t)((key - KEY_R1) / 2 + 1);
    if (!rotorToggleSelect(machineConfig, rotorId)) {
      printLcdLine(2, "Max 4 rotores");
      delay(600);
      printLcdLine(2, "");
    }
    updateRotorLine();
    if (uiMode == MODE_ENCRYPT && plainCompose.length() > 0) {
      snapshotCompositionStart();
      refreshEncryptDisplay();
    }
    return true;
  }

  if (key >= KEY_S1 && key <= KEY_S4) {
    uint8_t slotIndex = (uint8_t)(key - KEY_S1);
    rotorShiftRight(machineConfig, slotIndex);
    updateRotorLine();
    if (uiMode == MODE_ENCRYPT && plainCompose.length() > 0) {
      snapshotCompositionStart();
      refreshEncryptDisplay();
    }
    return true;
  }

  return false;
}

void handleKey(char key) {
  if (key == KEY_NONE) {
    return;
  }

  if (key == KEY_MODE) {
    if (uiMode == MODE_DECRYPT) {
      enterEncryptMode();
    } else {
      enterDecryptMode();
    }
    return;
  }

  if (key == KEY_RESET) {
    handleReset();
    return;
  }

  if (key == KEY_SYNC) {
    handleSync();
    return;
  }

  if (handleRotorKey(key)) {
    return;
  }

  if (uiMode == MODE_DECRYPT) {
    if (isLetter(key)) {
      printLcdLine(2, "DEC: letras inativas");
    }
    return;
  }

  // MODE_ENCRYPT
  if (key == KEY_SEND) {
    handleSend();
    return;
  }

  if (isLetter(key)) {
    if (machineConfig.slotCount == 0) {
      printLcdLine(2, "Sem rotores");
      return;
    }
    if (plainCompose.length() < MAX_PLAIN_LEN) {
      if (plainCompose.length() == 0) {
        snapshotCompositionStart();
      }
      plainCompose += (char)toupper(key);
      refreshEncryptDisplay();
      if (line1Cipher.length() > 0) {
        char lastCipher = line1Cipher.charAt(line1Cipher.length() - 1);
        showLetterOnBinaryLeds(lastCipher, BINARY_LED_DISPLAY_MS);
      }
    }
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  initAllLeds();

  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println(F("ENIGMA: boot"));

  validateModeLeds();
  selfTestBinaryLeds();

  Serial.println(F("Se ve isto, o sketch esta a correr."));

  enigmaInitEmpty(machineConfig);

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

  char key3 = keypad3.getKey();
  if (key3 != NO_KEY) {
    debugKeyPress('3', key3);
    handleKey(key3);
  }
}
