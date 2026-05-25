/*
 * Teste minimo de hardware - Arduino Mega 2560
 *
 * Use ESTE sketch primeiro se LCD e LEDs nao funcionarem.
 * Abra esta pasta no Arduino IDE (nao enigma_machine).
 *
 * Biblioteca: LiquidCrystal I2C (Frank de Brabander)
 *
 * O que deve acontecer:
 * - LED onboard (L) pisca
 * - LEDs nos pinos 48, 50, 52 piscam
 * - Serial Monitor 115200 mostra mensagens
 * - LCD mostra "Teste LCD OK" (se I2C estiver correto)
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#include "config.h"
#include "letter_leds.h"

#define PIN_LED_1 PIN_LED_DECRYPT
#define PIN_LED_2 PIN_LED_ENCRYPT
#define PIN_LED_3 PIN_LED_MESSAGE

// Tente 0x27; se LCD vazio, mude para 0x3F e volte a carregar
#define LCD_ADDR 0x27

LiquidCrystal_I2C lcd(LCD_ADDR, 20, 4);

void blinkPin(uint8_t pin, uint16_t ms) {
  digitalWrite(pin, HIGH);
  delay(ms);
  digitalWrite(pin, LOW);
  delay(ms);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PIN_LED_1, OUTPUT);
  pinMode(PIN_LED_2, OUTPUT);
  pinMode(PIN_LED_3, OUTPUT);

  Serial.begin(115200);
  delay(800);
  Serial.println();
  Serial.println(F("=== TESTE HARDWARE ENIGMA ==="));
  Serial.println(F("Placa esperada: Arduino Mega 2560"));

  for (int n = 0; n < 5; n++) {
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.print(F("Piscada modo "));
    Serial.println(n + 1);
    blinkPin(PIN_LED_1, 200);
    blinkPin(PIN_LED_2, 200);
    blinkPin(PIN_LED_3, 200);
    digitalWrite(LED_BUILTIN, LOW);
    delay(300);
  }

  Serial.println(F("LEDs modo: se nao piscaram, verifique 48/50/52"));

  initLetterLeds();
  selfTestBinaryLeds();
  Serial.println(F("LEDs L1-L5: teste A-E (valores 1-5)"));
  Serial.println(F("LED onboard (L) deve ter piscado junto com os externos"));

  Wire.begin();
  delay(100);

  Serial.print(F("A testar LCD no endereco 0x"));
  Serial.println(LCD_ADDR, HEX);

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Teste LCD OK");
  lcd.setCursor(0, 1);
  lcd.print("Endereco 0x27");
  lcd.setCursor(0, 3);
  lcd.print("Mega pinos 20/21");

  Serial.println(F("LCD init() feito."));
  Serial.println(F("Se LCD vazio: gire contraste, teste 0x3F, confira SDA/SCL"));
}

void loop() {
  static unsigned long last = 0;
  if (millis() - last > 1000) {
    last = millis();
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }
}
