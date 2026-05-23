#include "enigma.h"

static const char ALPHABET[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

static const char *const ROTOR_WIRINGS[] = {
    "EKMFLGDQVZNTOWYHXUSPAIBRCJ",  // I
    "AJDKSIRUXBLHWTMCQGZNPYFVOE",  // II
    "BDFHJLCPRTXVZNYEIWGAKMUSQO",  // III
};

static const char REFLECTOR_B[] = "YRUHQSLDPXNGOKMIEBFZCWVJAT";

static int letterIndex(char c) {
  if (c >= 'A' && c <= 'Z') return c - 'A';
  if (c >= 'a' && c <= 'z') return c - 'a';
  return -1;
}

static void stepPositions(uint8_t positions[3]) {
  positions[2] = (positions[2] + 1) % 26;
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

static char processLetter(char letter, const EnigmaConfig &config, uint8_t positions[3]) {
  stepPositions(positions);

  int index = letterIndex(letter);
  if (index < 0) return '?';

  for (int i = 2; i >= 0; i--) {
    const char *wiring = ROTOR_WIRINGS[config.order[i]];
    index = passForward(index, wiring, positions[i]);
  }

  index = letterIndex(REFLECTOR_B[index]);

  for (int i = 0; i < 3; i++) {
    const char *wiring = ROTOR_WIRINGS[config.order[i]];
    index = passBackward(index, wiring, positions[i]);
  }

  return ALPHABET[index];
}

void enigmaSetDefaultOrder(EnigmaConfig &config) {
  config.order[0] = 0;
  config.order[1] = 1;
  config.order[2] = 2;
}

String enigmaProcessMessage(const String &message, EnigmaConfig &config) {
  uint8_t positions[3] = {
      config.positions[0],
      config.positions[1],
      config.positions[2],
  };

  String output = "";
  output.reserve(message.length());

  for (unsigned int i = 0; i < message.length(); i++) {
    char c = message.charAt(i);
    int idx = letterIndex(c);
    if (idx < 0) continue;

    char out = processLetter((char)toupper(c), config, positions);
    output += out;
  }

  config.positions[0] = positions[0];
  config.positions[1] = positions[1];
  config.positions[2] = positions[2];

  return output;
}
