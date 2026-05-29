import { FlatList, StyleSheet, Text, View } from 'react-native';

import { MessageHistoryItem } from '../models/types';

type Props = {
  items: MessageHistoryItem[];
  emptyLabel: string;
};

export function MessageHistoryList({ items, emptyLabel }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Histórico</Text>
      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        scrollEnabled={false}
        ListEmptyComponent={<Text style={styles.empty}>{emptyLabel}</Text>}
        renderItem={({ item }) => (
          <View style={styles.item}>
            <Text style={styles.plain}>{item.plainText}</Text>
            <Text style={styles.cipher}>{item.cipherText}</Text>
          </View>
        )}
      />
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
  empty: {
    color: '#64748b',
    lineHeight: 20,
  },
  item: {
    gap: 4,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  plain: {
    color: '#0f172a',
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 1,
  },
  cipher: {
    color: '#475569',
    fontWeight: '600',
    letterSpacing: 1,
  },
});
