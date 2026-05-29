import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

export type MainTab = 'receive' | 'send';

type Props = {
  activeTab: MainTab;
  onTabChange: (tab: MainTab) => void;
  onOpenLogs: () => void;
  onOpenSettings: () => void;
};

export function AppTopBar({ activeTab, onTabChange, onOpenLogs, onOpenSettings }: Props) {
  return (
    <View style={styles.container}>
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'receive' && styles.tabActive]}
          onPress={() => onTabChange('receive')}
        >
          <Text style={[styles.tabText, activeTab === 'receive' && styles.tabTextActive]}>
            Receive
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'send' && styles.tabActive]}
          onPress={() => onTabChange('send')}
        >
          <Text style={[styles.tabText, activeTab === 'send' && styles.tabTextActive]}>
            Send
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.iconButton} onPress={onOpenLogs} accessibilityLabel="Logs">
          <Text style={styles.iconGlyph}>☰</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.iconButton}
          onPress={onOpenSettings}
          accessibilityLabel="Configurações"
        >
          <Text style={styles.iconGlyph}>⚙</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  tabs: {
    flexDirection: 'row',
    gap: 6,
    flex: 1,
  },
  tab: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: '#f1f5f9',
  },
  tabActive: {
    backgroundColor: '#1d4ed8',
  },
  tabText: {
    color: '#475569',
    fontWeight: '800',
  },
  tabTextActive: {
    color: '#ffffff',
  },
  actions: {
    flexDirection: 'row',
    gap: 4,
    marginLeft: 8,
  },
  iconButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    backgroundColor: '#f8fafc',
  },
  iconGlyph: {
    color: '#0f172a',
    fontSize: 18,
    fontWeight: '700',
  },
});
