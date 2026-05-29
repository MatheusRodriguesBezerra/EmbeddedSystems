import { FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { HttpLogItem } from '../models/types';
import { useAppStore } from '../store/useAppStore';

function formatJson(value: unknown) {
  if (value === undefined) {
    return undefined;
  }

  return JSON.stringify(value, null, 2);
}

function LogCard({ item }: { item: HttpLogItem }) {
  const isSuccess = item.status === 'success';
  const requestBody = formatJson(item.requestBody);
  const responseBody = formatJson(item.responseBody);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={[styles.badge, isSuccess ? styles.successBadge : styles.errorBadge]}>
          {item.status.toUpperCase()}
        </Text>
        <Text style={styles.method}>{item.method}</Text>
        <Text style={styles.duration}>{item.durationMs} ms</Text>
      </View>

      <Text style={styles.url}>{item.url}</Text>
      <Text style={styles.time}>{new Date(item.createdAt).toLocaleString()}</Text>

      {requestBody && (
        <View style={styles.block}>
          <Text style={styles.blockTitle}>Pedido</Text>
          <Text style={styles.monospace}>{requestBody}</Text>
        </View>
      )}

      {responseBody && (
        <View style={styles.block}>
          <Text style={styles.blockTitle}>Resposta</Text>
          <Text style={styles.monospace}>{responseBody}</Text>
        </View>
      )}

      {item.error && (
        <View style={styles.block}>
          <Text style={styles.blockTitle}>Erro</Text>
          <Text style={styles.errorText}>{item.error}</Text>
        </View>
      )}
    </View>
  );
}

export function LogsPanel() {
  const { httpLogs, clearHttpLogs } = useAppStore();

  return (
    <View style={styles.screen}>
      <View style={styles.toolbar}>
        <Text style={styles.subtitle}>Pedidos recentes</Text>
        <TouchableOpacity style={styles.clearButton} onPress={clearHttpLogs}>
          <Text style={styles.clearButtonText}>Limpar</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={httpLogs}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>Sem logs ainda</Text>
            <Text style={styles.emptyText}>
              Teste a ligação, envie ou receba uma mensagem para gerar registos.
            </Text>
          </View>
        }
        renderItem={({ item }) => <LogCard item={item} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#eef2f7',
  },
  toolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  subtitle: {
    color: '#475569',
    fontWeight: '700',
  },
  clearButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: '#e2e8f0',
  },
  clearButtonText: {
    color: '#0f172a',
    fontWeight: '800',
  },
  list: {
    gap: 12,
    padding: 16,
    paddingTop: 0,
  },
  card: {
    gap: 10,
    padding: 16,
    borderRadius: 16,
    backgroundColor: '#ffffff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  badge: {
    overflow: 'hidden',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: '900',
  },
  successBadge: {
    color: '#166534',
    backgroundColor: '#dcfce7',
  },
  errorBadge: {
    color: '#991b1b',
    backgroundColor: '#fee2e2',
  },
  method: {
    color: '#1d4ed8',
    fontWeight: '900',
  },
  duration: {
    marginLeft: 'auto',
    color: '#64748b',
    fontWeight: '700',
  },
  url: {
    color: '#0f172a',
    fontWeight: '700',
  },
  time: {
    color: '#64748b',
    fontSize: 12,
  },
  block: {
    gap: 6,
    padding: 10,
    borderRadius: 12,
    backgroundColor: '#f8fafc',
  },
  blockTitle: {
    color: '#475569',
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  monospace: {
    color: '#0f172a',
    fontFamily: 'monospace',
    fontSize: 12,
  },
  errorText: {
    color: '#b3261e',
    fontWeight: '700',
  },
  emptyCard: {
    gap: 8,
    padding: 16,
    borderRadius: 16,
    backgroundColor: '#ffffff',
  },
  emptyTitle: {
    color: '#0f172a',
    fontSize: 18,
    fontWeight: '800',
  },
  emptyText: {
    color: '#64748b',
    lineHeight: 20,
  },
});
