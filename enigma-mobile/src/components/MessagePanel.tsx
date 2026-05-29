import { StyleSheet, Text, View } from 'react-native';

type Props = {
  title: string;
  value: string;
  muted?: boolean;
};

export function MessagePanel({ title, value, muted }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <Text style={[styles.value, muted && styles.muted]}>{value || 'Sem mensagem'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: 8,
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#d6dee8',
    backgroundColor: '#ffffff',
  },
  title: {
    color: '#64748b',
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  value: {
    minHeight: 28,
    color: '#0f172a',
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  muted: {
    color: '#64748b',
  },
});
