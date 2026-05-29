import { StyleSheet, Text, View } from 'react-native';

import { useAppStore } from '../store/useAppStore';

const LABELS = {
  unknown: 'Não verificado',
  checking: 'Verificando...',
  connected: 'Conectado',
  disconnected: 'Desconectado',
};

export function ConnectionStatus() {
  const { connection, connectedArduino, raspberryAddress } = useAppStore();
  const isConnected = connection === 'connected';

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={[styles.dot, isConnected ? styles.dotOnline : styles.dotOffline]} />
        <Text style={styles.title}>{LABELS[connection]}</Text>
        <Text style={styles.meta}>
          {connectedArduino ? 'Arduino OK' : 'Arduino ?'} · {raspberryAddress || 'sem IP'}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#f8fafc',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  dotOnline: {
    backgroundColor: '#18864b',
  },
  dotOffline: {
    backgroundColor: '#b3261e',
  },
  title: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0f172a',
  },
  meta: {
    marginLeft: 'auto',
    color: '#64748b',
    fontSize: 12,
    fontWeight: '600',
  },
});
