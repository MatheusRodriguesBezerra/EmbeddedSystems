#ifndef ENIGMA_H
#define ENIGMA_H

#include <Arduino.h>
#include "config.h"

struct EnigmaConfig {
  uint8_t slotRotor[MAX_ACTIVE_ROTORS];  // 0=vazio, 1-6 = R1-R6
  uint8_t slotPos[MAX_ACTIVE_ROTORS];
  uint8_t slotCount;
  uint8_t pendingPos[ROTOR_POOL_SIZE];   // posicao ajustada via R[N]+ antes/durante selecao
};

void enigmaInitEmpty(EnigmaConfig &config);

// Processa mensagem A-Z; atualiza slotPos ao final
String enigmaProcessMessage(const String &message, EnigmaConfig &config);

#endif
