import { MachineConfig, RotorNumber, RotorSlot } from '../models/types';

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

const ROTOR_WIRINGS: Record<RotorNumber, string> = {
  1: 'EKMFLGDQVZNTOWYHXUSPAIBRCJ',
  2: 'AJDKSIRUXBLHWTMCQGZNPYFVOE',
  3: 'BDFHJLCPRTXVZNYEIWGAKMUSQO',
  4: 'ESLPYHKWRDAVZFXNGMJCQIOBUT',
  5: 'VZBRGITYUPSDNHLXAWMJQOFECK',
  6: 'JVMUBRFXDYZNTQEWHGLKOCPISA',
};

const REFLECTOR_B = 'YRUHQSLDPXNGOKMIEBFZCWVJAT';

function toIndex(letter: string) {
  return ALPHABET.indexOf(letter);
}

function stepPositions(positions: number[]) {
  if (positions.length === 0) {
    return positions;
  }
  const next = [...positions];
  next[next.length - 1] = (next[next.length - 1] + 1) % 26;
  return next;
}

function passForward(index: number, wiring: string, position: number) {
  const shifted = (index + position) % 26;
  const mapped = toIndex(wiring[shifted]);
  return (mapped - position + 26) % 26;
}

function passBackward(index: number, wiring: string, position: number) {
  const shifted = (index + position) % 26;
  const mapped = wiring.indexOf(ALPHABET[shifted]);
  return (mapped - position + 26) % 26;
}

function processLetter(letter: string, rotors: RotorSlot[], positions: number[]) {
  const nextPositions = stepPositions(positions);
  let index = toIndex(letter);
  const count = rotors.length;

  for (let rotorIndex = count - 1; rotorIndex >= 0; rotorIndex -= 1) {
    index = passForward(index, ROTOR_WIRINGS[rotors[rotorIndex].id], nextPositions[rotorIndex]);
  }

  index = toIndex(REFLECTOR_B[index]);

  for (let rotorIndex = 0; rotorIndex < count; rotorIndex += 1) {
    index = passBackward(index, ROTOR_WIRINGS[rotors[rotorIndex].id], nextPositions[rotorIndex]);
  }

  return {
    output: ALPHABET[index],
    positions: nextPositions,
  };
}

export function processEnigmaMessage(message: string, config: MachineConfig) {
  if (config.rotors.length === 0) {
    return {
      output: '',
      rotors: [] as RotorSlot[],
    };
  }

  let positions = config.rotors.map((slot) => slot.position);
  let output = '';

  for (const letter of message) {
    const result = processLetter(letter, config.rotors, positions);
    output += result.output;
    positions = result.positions;
  }

  const rotors = config.rotors.map((slot, index) => ({
    id: slot.id,
    position: positions[index],
  }));

  return {
    output,
    rotors,
  };
}

export function formatRotorLine(rotors: RotorSlot[]) {
  return rotors.map((slot) => `${slot.id}:${slot.position}`).join(' ');
}
