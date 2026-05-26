#ifndef ROTOR_BANK_H
#define ROTOR_BANK_H

#include "enigma.h"

void rotorFormatLine(const EnigmaConfig &config, char *buf, size_t bufSize);
void rotorFormatSlotsCsv(const EnigmaConfig &config, char *buf, size_t bufSize);
int8_t rotorFindSlot(const EnigmaConfig &config, uint8_t rotorId);
bool rotorToggleSelect(EnigmaConfig &config, uint8_t rotorId);
void rotorIncrementPending(EnigmaConfig &config, uint8_t rotorId);
void rotorShiftRight(EnigmaConfig &config, uint8_t slotIndex);
void rotorClearAll(EnigmaConfig &config);
bool rotorApplyPosLine(EnigmaConfig &config, const String &line);

#endif
