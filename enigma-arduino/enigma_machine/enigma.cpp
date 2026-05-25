#include "enigma.h"

static const char ALPHABET[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

static const char *const ROTOR_WIRINGS[] = {
    "EKMFLGDQVZNTOWYHXUSPAIBRCJ",  // R1 / I
    "AJDKSIRUXBLHWTMCQGZNPYFVOE",  // R2 / II
    "BDFHJLCPRTXVZNYEIWGAKMUSQO",  // R3 / III
    "ESLPYHKWRDAVZFXNGMJCQIOBUT",  // R4 / IV
    "VZBRGRIYWATUKQCMLHPFDJNCXESO",  // R5 / V
    "JVMUBRFXDYZNTQEWHGLKOCPISA",  // R6 / VI
};

static const char REFLECTOR_B[] = "YRUHQSLDPXNGOKMIEBFZCWVJAT";

static int letterIndex(char c) {
  if (c >= 'A' && c <= 'Z') return c - 'A';
  if (c >= 'a' && c <= 'z') return c - 'a';
  return -1;
}

static void stepPositions(uint8_t positions[], uint8_t count) {
  if (count == 0) return;
  positions[count - 1] = (positions[count - 1] + 1) % 26;
}

static int passForward(int index, const char *wiring, uint8_t position) {
  int shifted = (index + position) % 26;
  int mapped = letterIndex(wiring[shifted]);
  return (mapped - position + 26) % 26;
}

static int passBackward(int index, const char *wiring, uint8_t position) {
  int shifted = (index + position) % 26;
  char ch = ALPHABET[shifted];
  const char *found = strchr(wiring, ch);
  if (!found) return 0;
  int mapped = found - wiring;
  return (mapped - position + 26) % 26;
}

static char processLetter(
    char letter,
    const uint8_t slotRotor[],
    uint8_t positions[],
    uint8_t count) {
  stepPositions(positions, count);

  int index = letterIndex(letter);
  if (index < 0 || count == 0) return '?';

  for (int i = count - 1; i >= 0; i--) {
    const char *wiring = ROTOR_WIRINGS[slotRotor[i] - 1];
    index = passForward(index, wiring, positions[i]);
  }

  index = letterIndex(REFLECTOR_B[index]);

  for (uint8_t i = 0; i < count; i++) {
    const char *wiring = ROTOR_WIRINGS[slotRotor[i] - 1];
    index = passBackward(index, wiring, positions[i]);
  }

  return ALPHABET[index];
}

void enigmaInitEmpty(EnigmaConfig &config) {
  config.slotCount = 0;
  for (uint8_t i = 0; i < MAX_ACTIVE_ROTORS; i++) {
    config.slotRotor[i] = 0;
    config.slotPos[i] = 0;
  }
  for (uint8_t i = 0; i < ROTOR_POOL_SIZE; i++) {
    config.pendingPos[i] = 0;
  }
}

String enigmaProcessMessage(const String &message, EnigmaConfig &config) {
  if (config.slotCount == 0) {
    return "";
  }

  uint8_t positions[MAX_ACTIVE_ROTORS];
  for (uint8_t i = 0; i < config.slotCount; i++) {
    positions[i] = config.slotPos[i];
  }

  String output = "";
  output.reserve(message.length());

  for (unsigned int i = 0; i < message.length(); i++) {
    char c = message.charAt(i);
    if (letterIndex(c) < 0) continue;

    char out = processLetter(
        (char)toupper(c),
        config.slotRotor,
        positions,
        config.slotCount);
    output += out;
  }

  for (uint8_t i = 0; i < config.slotCount; i++) {
    config.slotPos[i] = positions[i];
  }

  return output;
}
