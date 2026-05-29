import { RotorNumber, RotorSlot } from '../models/types';

export const ROTOR_IDS: RotorNumber[] = [1, 2, 3, 4, 5, 6];
export const MAX_ACTIVE_ROTORS = 4;

export function sanitizeMessage(value: string) {
  return value.toUpperCase().replace(/[^A-Z]/g, '');
}

export function isValidRaspberryAddress(value: string) {
  const trimmed = value.trim();
  return trimmed.length > 0 && !/\s/.test(trimmed);
}

export function normalizeBaseUrl(value: string) {
  const trimmed = value.trim().replace(/\/+$/, '');

  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed;
  }

  return `http://${trimmed}`;
}

export function clampRotorPosition(value: number) {
  if (Number.isNaN(value)) {
    return 0;
  }

  return Math.min(25, Math.max(0, Math.round(value)));
}

export function isValidRotorConfig(rotors: RotorSlot[]) {
  if (rotors.length > MAX_ACTIVE_ROTORS) {
    return false;
  }

  const ids = rotors.map((slot) => slot.id);
  return new Set(ids).size === ids.length && ids.every((id) => id >= 1 && id <= 6);
}

export function findSlotIndex(rotors: RotorSlot[], rotorId: RotorNumber) {
  return rotors.findIndex((slot) => slot.id === rotorId);
}

export function toggleRotorSelection(rotors: RotorSlot[], rotorId: RotorNumber) {
  const existingIndex = findSlotIndex(rotors, rotorId);
  if (existingIndex >= 0) {
    return rotors.filter((_, index) => index !== existingIndex);
  }

  if (rotors.length >= MAX_ACTIVE_ROTORS) {
    return rotors;
  }

  return [...rotors, { id: rotorId, position: 0 }];
}

export function incrementRotorPosition(rotors: RotorSlot[], rotorId: RotorNumber) {
  const existingIndex = findSlotIndex(rotors, rotorId);
  if (existingIndex < 0) {
    return rotors;
  }

  return rotors.map((slot, index) =>
    index === existingIndex
      ? { ...slot, position: (slot.position + 1) % 26 }
      : slot,
  );
}

export function shiftSlotRight(rotors: RotorSlot[], slotIndex: number) {
  if (slotIndex < 0 || slotIndex + 1 >= rotors.length) {
    return rotors;
  }

  const next = [...rotors];
  [next[slotIndex], next[slotIndex + 1]] = [next[slotIndex + 1], next[slotIndex]];
  return next;
}

export function updateSlotPosition(rotors: RotorSlot[], slotIndex: number, position: number) {
  return rotors.map((slot, index) =>
    index === slotIndex ? { ...slot, position: clampRotorPosition(position) } : slot,
  );
}
