/*
 * Enigma Machine - Arduino Mega 2560
 * Consulte README.md para o protocolo serial e o comportamento esperado.
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

// ----- Keypads -----
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

// Keypad 2: letras Q-Z + comandos. LOCK ocupa linha 3 coluna 3.
const byte KP2_ROWS = 4;
const byte KP2_COLS = 4;
char keys2[KP2_ROWS][KP2_COLS] = {
    {'Q', 'R', 'S', 'T'},
    {'U', 'V', 'W', 'X'},
    {'Y', 'Z', KEY_LOCK, KEY_NONE},
    {KEY_SYNC, KEY_RESET, KEY_MODE, KEY_SEND},
};
byte rowPins2[KP2_ROWS] = {30, 31, 32, 33};
byte colPins2[KP2_COLS] = {34, 35, 36, 37};
Keypad keypad2 = Keypad(makeKeymap(keys2), rowPins2, colPins2, KP2_ROWS, KP2_COLS);

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

// ----- Estado -----
UiMode uiMode = MODE_ENCRYPT;
EnigmaConfig machineConfig;
String plainCompose = "";
String line1Cipher = "";
String line2Plain = "";

// Para refrescar a cifra na composicao quando rotores mudam.
uint8_t compositionStartPos[MAX_ACTIVE_ROTORS] = {0, 0, 0, 0};
uint8_t compositionStartCount = 0;

// Linha serial em construcao.
char serialLine[96];
uint8_t serialLineLen = 0;

unsigned long syncDeadline = 0;
bool awaitingSyncResponse = false;
bool lcdReady = false;

// LOCK gate: enquanto false, as letras nao sao aceitas.
bool locked = false;
// Mensagem em curso (LED MSG aceso).
bool messageActive = false;

void setModeLeds();
void printLcdLine(uint8_t row, const String &text);
void updateRotorLine();
void clearMessageLines();
void enterEncryptMode();
void enterDecryptMode();
void clearLock(const __FlashStringHelper *reason);

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
    Serial.println(F("  NENHUM dispositivo I2C encontrado."));
  }
  Serial.println(F("--------------------------------"));
}

void setModeLeds() {
  digitalWrite(PIN_LED_DECRYPT, (uiMode == MODE_DECRYPT) ? LED_ON : LED_OFF);
  digitalWrite(PIN_LED_ENCRYPT, (uiMode == MODE_ENCRYPT) ? LED_ON : LED_OFF);
  digitalWrite(PIN_LED_MESSAGE, messageActive ? LED_ON : LED_OFF);
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
  for (uint8_t i = 0; i < LCD_COLS; i++) {
    lcd.print(' ');
  }
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
  printLcdLine(0, "");
  printLcdLine(1, "");
}

void snapshotCompositionStart() {
  compositionStartCount = machineConfig.slotCount;
  for (uint8_t i = 0; i < MAX_ACTIVE_ROTORS; i++) {
    compositionStartPos[i] = (i < compositionStartCount) ? machineConfig.slotPos[i] : 0;
  }
}

void refreshEncryptDisplay() {
  if (plainCompose.length() == 0 || machineConfig.slotCount == 0) {
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

void clearLock(const __FlashStringHelper *reason) {
  if (!locked) return;
  locked = false;
  if (reason != nullptr) {
    printLcdLine(2, reason);
  }
}

void enterEncryptMode() {
  uiMode = MODE_ENCRYPT;
  plainCompose = "";
  clearMessageLines();
  locked = false;
  messageActive = false;
  printLcdLine(2, F("CIFRAR (LOCK?)"));
  updateRotorLine();
  setModeLeds();
  Serial.println(F("MODE:ENC"));
}

void enterDecryptMode() {
  uiMode = MODE_DECRYPT;
  plainCompose = "";
  clearMessageLines();
  locked = false;
  messageActive = false;
  printLcdLine(2, F("DECIFRAR (LOCK?)"));
  updateRotorLine();
  setModeLeds();
  Serial.println(F("MODE:DEC"));
}

void requestSync() {
  Serial.println(F("SYNC"));
  awaitingSyncResponse = true;
  syncDeadline = millis() + SYNC_TIMEOUT_MS;
  printLcdLine(2, F("SYNC..."));
}

void finishSync(bool gotCfg) {
  awaitingSyncResponse = false;
  if (!gotCfg) {
    printLcdLine(2, F("SYNC: sem resposta"));
  } else {
    printLcdLine(2, F("SYNC: OK"));
  }
}

void handleReset() {
  plainCompose = "";
  clearMessageLines();
  rotorClearAll(machineConfig);
  updateRotorLine();
  locked = false;
  messageActive = false;
  setModeLeds();
  printLcdLine(2, F("RESET"));
}

void handleLock() {
  if (machineConfig.slotCount == 0) {
    printLcdLine(2, F("Sem rotores"));
    return;
  }
  locked = true;
  if (uiMode == MODE_ENCRYPT) {
    printLcdLine(2, F("LOCK: digite letras"));
  } else {
    printLcdLine(2, F("LOCK: aguardando..."));
  }
}

void handleSendInEncrypt() {
  if (!locked || plainCompose.length() == 0) return;
  if (machineConfig.slotCount == 0) {
    printLcdLine(2, F("Sem rotores"));
    return;
  }

  refreshEncryptDisplay();
  Serial.print(F("MESSAGEFROMARDUINO:"));
  Serial.println(line1Cipher);

  messageActive = true;
  setModeLeds();
  printLcdLine(2, F("Enviando..."));
  delay(SEND_MESSAGE_LED_MS);

  messageActive = false;
  handleReset();
}

void applyDecryptPayload(const String &payload) {
  String clean = "";
  for (unsigned int i = 0; i < payload.length(); i++) {
    char c = toupper(payload.charAt(i));
    if (c >= 'A' && c <= 'Z') clean += c;
  }
  if (clean.length() == 0) return;
  if (!locked) {
    printLcdLine(2, F("Cifra ignorada (LOCK?)"));
    return;
  }
  if (machineConfig.slotCount == 0) {
    printLcdLine(2, F("Sem rotores"));
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
  setModeLeds();
  printLcdLine(2, F("Mensagem recebida"));

  playDecryptLetterSequence(line2Plain.c_str(), BINARY_LED_DISPLAY_MS, DECRYPT_FINISH_ALL_MS);
}

void handleSerialLine(const String &line) {
  if (line.startsWith(F("POS:"))) {
    if (rotorApplyPosLine(machineConfig, line)) {
      updateRotorLine();
      finishSync(true);
    }
    return;
  }

  if (line.startsWith(F("MESSAGEFROMMOBILE:"))) {
    if (uiMode == MODE_DECRYPT) {
      applyDecryptPayload(line.substring(18));
    } else {
      printLcdLine(2, F("Mensagem ignorada (ENC)"));
    }
    return;
  }

  if (line.startsWith(F("STATUS:"))) {
    return;
  }

  if (line.startsWith(F("ACK:"))) {
    return;
  }

  if (line.startsWith(F("ERR:"))) {
    String tail = line.substring(4);
    if (tail.length() > LCD_COLS) tail = tail.substring(0, LCD_COLS);
    printLcdLine(2, "ERR: " + tail);
    return;
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

  if (awaitingSyncResponse && (long)(millis() - syncDeadline) > 0) {
    finishSync(false);
  }
}

bool isLetter(char key) {
  return (key >= 'A' && key <= 'Z') || (key >= 'a' && key <= 'z');
}

bool handleRotorKey(char key) {
  if (key >= KEY_R1_PLUS && key <= KEY_R6_PLUS && ((key - KEY_R1_PLUS) % 2 == 0)) {
    uint8_t rotorId = (uint8_t)((key - KEY_R1_PLUS) / 2 + 1);
    rotorIncrementPending(machineConfig, rotorId);
    updateRotorLine();
    clearLock(F("LOCK perdido"));
    if (uiMode == MODE_ENCRYPT && plainCompose.length() > 0) {
      snapshotCompositionStart();
      refreshEncryptDisplay();
    }
    return true;
  }

  if (key >= KEY_R1 && key <= KEY_R6 && ((key - KEY_R1) % 2 == 0)) {
    uint8_t rotorId = (uint8_t)((key - KEY_R1) / 2 + 1);
    if (!rotorToggleSelect(machineConfig, rotorId)) {
      printLcdLine(2, F("Max 4 rotores"));
      return true;
    }
    updateRotorLine();
    clearLock(F("LOCK perdido"));
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
    clearLock(F("LOCK perdido"));
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
    if (uiMode == MODE_ENCRYPT) {
      enterDecryptMode();
    } else {
      enterEncryptMode();
    }
    return;
  }

  if (key == KEY_RESET) {
    handleReset();
    return;
  }

  if (key == KEY_SYNC) {
    requestSync();
    return;
  }

  if (key == KEY_LOCK) {
    handleLock();
    return;
  }

  if (handleRotorKey(key)) {
    return;
  }

  if (uiMode == MODE_DECRYPT) {
    if (isLetter(key)) {
      printLcdLine(2, F("DEC: letras inativas"));
    }
    return;
  }

  // MODE_ENCRYPT
  if (key == KEY_SEND) {
    handleSendInEncrypt();
    return;
  }

  if (isLetter(key)) {
    if (!locked) {
      printLcdLine(2, F("Pressione LOCK"));
      return;
    }
    if (machineConfig.slotCount == 0) {
      printLcdLine(2, F("Sem rotores"));
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
    } else {
      printLcdLine(2, F("Limite 20 chars"));
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

  enigmaInitEmpty(machineConfig);

  Wire.begin();
  delay(100);
  scanI2CBus();

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcdReady = true;

  printLcdLine(0, F("Enigma iniciado"));
  updateRotorLine();
  enterEncryptMode();
  Serial.println(F("ENIGMA: pronto (modo ENC)"));
}

void loop() {
  pollSerial();

  char key1 = keypad1.getKey();
  if (key1 != NO_KEY) handleKey(key1);

  char key2 = keypad2.getKey();
  if (key2 != NO_KEY) handleKey(key2);

  char key3 = keypad3.getKey();
  if (key3 != NO_KEY) handleKey(key3);
}
