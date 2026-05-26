#include "rotor_bank.h"

void rotorFormatLine(const EnigmaConfig &config, char *buf, size_t bufSize) {
  buf[0] = '\0';
  size_t offset = 0;

  for (uint8_t i = 0; i < config.slotCount; i++) {
    if (offset >= bufSize - 1) break;
    int written = snprintf(
        buf + offset,
        bufSize - offset,
        "%s%u:%u",
        (i == 0) ? "" : " ",
        config.slotRotor[i],
        config.slotPos[i]);
    if (written < 0) break;
    offset += (size_t)written;
  }
}

void rotorFormatSlotsCsv(const EnigmaConfig &config, char *buf, size_t bufSize) {
  buf[0] = '\0';
  size_t offset = 0;

  for (uint8_t i = 0; i < config.slotCount; i++) {
    if (offset >= bufSize - 1) break;
    int written = snprintf(
        buf + offset,
        bufSize - offset,
        "%s%u,%u",
        (i == 0) ? "" : ",",
        config.slotRotor[i],
        config.slotPos[i]);
    if (written < 0) break;
    offset += (size_t)written;
  }
}

int8_t rotorFindSlot(const EnigmaConfig &config, uint8_t rotorId) {
  for (uint8_t i = 0; i < config.slotCount; i++) {
    if (config.slotRotor[i] == rotorId) {
      return (int8_t)i;
    }
  }
  return -1;
}

bool rotorToggleSelect(EnigmaConfig &config, uint8_t rotorId) {
  if (rotorId < 1 || rotorId > ROTOR_POOL_SIZE) {
    return false;
  }

  int8_t slot = rotorFindSlot(config, rotorId);
  if (slot >= 0) {
    for (uint8_t i = (uint8_t)slot; i < config.slotCount - 1; i++) {
      config.slotRotor[i] = config.slotRotor[i + 1];
      config.slotPos[i] = config.slotPos[i + 1];
    }
    config.slotCount--;
    config.slotRotor[config.slotCount] = 0;
    config.slotPos[config.slotCount] = 0;
    return true;
  }

  if (config.slotCount >= MAX_ACTIVE_ROTORS) {
    return false;
  }

  config.slotRotor[config.slotCount] = rotorId;
  config.slotPos[config.slotCount] = config.pendingPos[rotorId - 1];
  config.slotCount++;
  return true;
}

void rotorIncrementPending(EnigmaConfig &config, uint8_t rotorId) {
  if (rotorId < 1 || rotorId > ROTOR_POOL_SIZE) {
    return;
  }

  config.pendingPos[rotorId - 1] = (config.pendingPos[rotorId - 1] + 1) % 26;

  int8_t slot = rotorFindSlot(config, rotorId);
  if (slot >= 0) {
    config.slotPos[slot] = config.pendingPos[rotorId - 1];
  }
}

void rotorShiftRight(EnigmaConfig &config, uint8_t slotIndex) {
  if (slotIndex >= config.slotCount || slotIndex + 1 >= config.slotCount) {
    return;
  }

  uint8_t next = slotIndex + 1;
  uint8_t tmpRotor = config.slotRotor[slotIndex];
  uint8_t tmpPos = config.slotPos[slotIndex];
  config.slotRotor[slotIndex] = config.slotRotor[next];
  config.slotPos[slotIndex] = config.slotPos[next];
  config.slotRotor[next] = tmpRotor;
  config.slotPos[next] = tmpPos;
}

void rotorClearAll(EnigmaConfig &config) {
  enigmaInitEmpty(config);
}

bool rotorApplyPosLine(EnigmaConfig &config, const String &line) {
  int p = line.indexOf("POS:");
  if (p < 0) return false;

  String rest = line.substring(p + 4);
  rest.trim();
  enigmaInitEmpty(config);

  if (rest.length() == 0) {
    return true;
  }

  int start = 0;
  while (start < rest.length() && config.slotCount < MAX_ACTIVE_ROTORS) {
    int comma = rest.indexOf(',', start);
    if (comma < 0) return false;

    int rotorId = rest.substring(start, comma).toInt();
    start = comma + 1;

    comma = rest.indexOf(',', start);
    int posEnd = (comma < 0) ? rest.length() : comma;
    int position = rest.substring(start, posEnd).toInt();
    start = (comma < 0) ? rest.length() : comma + 1;

    if (rotorId < 1 || rotorId > ROTOR_POOL_SIZE) {
      return false;
    }
    if (rotorFindSlot(config, (uint8_t)rotorId) >= 0) {
      return false;
    }

    config.slotRotor[config.slotCount] = (uint8_t)rotorId;
    config.slotPos[config.slotCount] = constrain(position, 0, 25);
    config.pendingPos[rotorId - 1] = config.slotPos[config.slotCount];
    config.slotCount++;
  }

  return true;
}
