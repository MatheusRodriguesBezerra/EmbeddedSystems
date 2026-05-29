import { EnigmaMode } from '../models/types';

export function getModeLabel(mode: EnigmaMode) {
  return mode === 'ENC' ? 'Cifrar' : 'Decifrar';
}
