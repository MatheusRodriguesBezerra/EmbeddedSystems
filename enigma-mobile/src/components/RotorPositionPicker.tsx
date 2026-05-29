import { StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { clampRotorPosition } from '../utils/validators';

type Props = {
  label: string;
  value: number;
  onChange: (value: number) => void;
};

export function RotorPositionPicker({ label, value, onChange }: Props) {
  function update(nextValue: number) {
    onChange(clampRotorPosition(nextValue));
  }

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.controls}>
        <TouchableOpacity style={styles.button} onPress={() => update(value - 1)}>
          <Text style={styles.buttonText}>-</Text>
        </TouchableOpacity>
        <TextInput
          keyboardType="number-pad"
          maxLength={2}
          style={styles.input}
          value={String(value)}
          onChangeText={(text) => update(Number(text))}
        />
        <TouchableOpacity style={styles.button} onPress={() => update(value + 1)}>
          <Text style={styles.buttonText}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 8,
  },
  label: {
    color: '#334155',
    fontWeight: '700',
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  button: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    backgroundColor: '#e2e8f0',
  },
  buttonText: {
    color: '#0f172a',
    fontSize: 20,
    fontWeight: '700',
  },
  input: {
    width: 64,
    height: 44,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 12,
    textAlign: 'center',
    color: '#0f172a',
    fontSize: 16,
    fontWeight: '700',
  },
});
