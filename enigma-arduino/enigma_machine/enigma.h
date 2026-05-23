#ifndef ENIGMA_H
#define ENIGMA_H

#include <Arduino.h>

// Ordem default: I, II, III (indices 0, 1, 2)
struct EnigmaConfig {
  uint8_t order[3];
  uint8_t positions[3];
};

void enigmaSetDefaultOrder(EnigmaConfig &config);

// Processa mensagem A-Z; atualiza positions ao final
String enigmaProcessMessage(const String &message, EnigmaConfig &config);

#endif
