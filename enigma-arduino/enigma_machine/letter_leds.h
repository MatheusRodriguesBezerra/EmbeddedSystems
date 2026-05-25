#ifndef LETTER_LEDS_H
#define LETTER_LEDS_H

#include <Arduino.h>

#include "config.h"

void initAllLeds();
void clearBinaryLeds();
void setAllBinaryLeds(bool on);
void setBinaryValue(uint8_t value);
uint8_t letterToBinaryValue(char letter);
void showLetterOnBinaryLeds(char letter, uint16_t durationMs);
void validateModeLeds();
void selfTestBinaryLeds();
void playDecryptLetterSequence(const char *plain, uint16_t letterMs, uint16_t allOnMs);

#endif
