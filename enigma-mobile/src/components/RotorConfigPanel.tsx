import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { RotorSlot } from '../models/types';
import { formatRotorLine } from '../services/enigmaMachine';
import {
  MAX_ACTIVE_ROTORS,
  ROTOR_IDS,
  findSlotIndex,
  incrementRotorPosition,
  shiftSlotRight,
  toggleRotorSelection,
} from '../utils/validators';
import { RotorPositionPicker } from './RotorPositionPicker';

type Props = {
  rotors: RotorSlot[];
  onChange: (rotors: RotorSlot[]) => void;
};

export function RotorConfigPanel({ rotors, onChange }: Props) {
  const atLimit = rotors.length >= MAX_ACTIVE_ROTORS;

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Selecione até {MAX_ACTIVE_ROTORS} rotores (R1–R6)</Text>
      <View style={styles.options}>
        {ROTOR_IDS.map((rotorId) => {
          const selected = findSlotIndex(rotors, rotorId) >= 0;
          const disabled = !selected && atLimit;

          return (
            <TouchableOpacity
              key={`rotor-${rotorId}`}
              style={[
                styles.option,
                selected && styles.optionSelected,
                disabled && styles.optionDisabled,
              ]}
              disabled={disabled}
              onPress={() => onChange(toggleRotorSelection(rotors, rotorId))}
            >
              <Text style={[styles.optionText, selected && styles.optionTextSelected]}>
                R{rotorId}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {rotors.length > 0 && (
        <>
          <Text style={styles.label}>Ordem atual: {formatRotorLine(rotors)}</Text>
          <View style={styles.shiftRow}>
            {[0, 1, 2, 3].map((slotIndex) => {
              const enabled = slotIndex + 1 < rotors.length;
              return (
                <TouchableOpacity
                  key={`shift-${slotIndex}`}
                  style={[styles.shiftButton, !enabled && styles.optionDisabled]}
                  disabled={!enabled}
                  onPress={() => onChange(shiftSlotRight(rotors, slotIndex))}
                >
                  <Text style={styles.shiftText}>S{slotIndex + 1}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text style={styles.label}>Posições iniciais</Text>
          {rotors.map((slot, index) => (
            <View key={`slot-${slot.id}-${index}`} style={styles.positionBlock}>
              <RotorPositionPicker
                label={`R${slot.id}`}
                value={slot.position}
                onChange={(value) =>
                  onChange(
                    rotors.map((current, currentIndex) =>
                      currentIndex === index ? { ...current, position: value } : current,
                    ),
                  )
                }
              />
              <TouchableOpacity
                style={styles.plusButton}
                onPress={() => onChange(incrementRotorPosition(rotors, slot.id))}
              >
                <Text style={styles.plusText}>R{slot.id}+</Text>
              </TouchableOpacity>
            </View>
          ))}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  label: {
    color: '#334155',
    fontWeight: '700',
  },
  options: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  option: {
    minWidth: 52,
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#cbd5e1',
  },
  optionSelected: {
    borderColor: '#1d4ed8',
    backgroundColor: '#dbeafe',
  },
  optionDisabled: {
    opacity: 0.45,
  },
  optionText: {
    color: '#334155',
    fontWeight: '700',
  },
  optionTextSelected: {
    color: '#1d4ed8',
  },
  shiftRow: {
    flexDirection: 'row',
    gap: 8,
  },
  shiftButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    backgroundColor: '#f8fafc',
  },
  shiftText: {
    color: '#0f172a',
    fontWeight: '800',
  },
  positionBlock: {
    gap: 8,
  },
  plusButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: '#e2e8f0',
  },
  plusText: {
    color: '#0f172a',
    fontWeight: '800',
  },
});
