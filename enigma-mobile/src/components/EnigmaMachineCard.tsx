import { StyleSheet, Text, View } from 'react-native';

import { MachineConfig } from '../models/types';
import { formatRotorLine } from '../services/enigmaMachine';
import { getModeLabel } from '../utils/displayText';

type Props = {
  config: MachineConfig;
};

export function EnigmaMachineCard({ config }: Props) {
  const rotorLine =
    config.rotors.length > 0 ? formatRotorLine(config.rotors) : 'Nenhum rotor selecionado';

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Máquina Enigma</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Operação</Text>
        <Text style={styles.value}>{getModeLabel(config.mode)}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Rotores</Text>
        <Text style={styles.value}>{rotorLine}</Text>
      </View>
      {config.rotors.length > 0 && (
        <View style={styles.positionsRow}>
          {config.rotors.map((slot, index) => (
            <View key={`rotor-${slot.id}-${index}`} style={styles.positionChip}>
              <Text style={styles.chipLabel}>R{slot.id}</Text>
              <Text style={styles.chipValue}>{slot.position}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: 10,
    padding: 16,
    borderRadius: 16,
    backgroundColor: '#ffffff',
  },
  title: {
    color: '#0f172a',
    fontSize: 18,
    fontWeight: '800',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  label: {
    color: '#64748b',
    fontWeight: '600',
  },
  value: {
    flex: 1,
    color: '#0f172a',
    fontWeight: '800',
    textAlign: 'right',
  },
  positionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  positionChip: {
    minWidth: 72,
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 12,
    backgroundColor: '#eff6ff',
  },
  chipLabel: {
    color: '#64748b',
    fontSize: 12,
    fontWeight: '700',
  },
  chipValue: {
    color: '#1d4ed8',
    fontSize: 20,
    fontWeight: '900',
  },
});
