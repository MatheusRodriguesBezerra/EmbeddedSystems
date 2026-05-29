import { useEffect, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AppTopBar, MainTab } from '../components/AppTopBar';
import { ConfigModal } from '../components/ConfigModal';
import { ConnectionStatus } from '../components/ConnectionStatus';
import { EnigmaMachineCard } from '../components/EnigmaMachineCard';
import { LogsModal } from '../components/LogsModal';
import { MessageHistoryList } from '../components/MessageHistoryList';
import { useConnection } from '../hooks/useConnection';
import { usePendingPoll } from '../hooks/usePendingPoll';
import { useAppStore } from '../store/useAppStore';
import { sanitizeMessage } from '../utils/validators';

export function HomeScreen() {
  const [activeTab, setActiveTab] = useState<MainTab>('send');
  const [configVisible, setConfigVisible] = useState(false);
  const [logsVisible, setLogsVisible] = useState(false);
  const [message, setMessage] = useState('');

  const { isBusy, ping, sendMessage } = useConnection();
  const { config, history, lastError, setMode } = useAppStore();

  const { isPolling, lastPollAt } = usePendingPoll({
    enabled: activeTab === 'receive',
    onMessageReceived: () => setActiveTab('send'),
  });

  useEffect(() => {
    setMode(activeTab === 'send' ? 'ENC' : 'DEC');
  }, [activeTab, setMode]);

  const sentHistory = history.filter((item) => item.direction === 'sent');
  const receivedHistory = history.filter((item) => item.direction === 'received');

  async function handleSend() {
    const sanitized = sanitizeMessage(message);
    const success = await sendMessage(sanitized);
    if (success) {
      setMessage('');
    }
  }

  function handleTabChange(tab: MainTab) {
    setActiveTab(tab);
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right']}>
      <AppTopBar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onOpenLogs={() => setLogsVisible(true)}
        onOpenSettings={() => setConfigVisible(true)}
      />
      <ConnectionStatus />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.select({ ios: 'padding', android: undefined })}
      >
        <ScrollView contentContainerStyle={styles.content}>
          <EnigmaMachineCard config={config} />

          {activeTab === 'send' ? (
            <View style={styles.panel}>
              <Text style={styles.sectionTitle}>Cifrar e enviar</Text>
              <Text style={styles.helpText}>
                O texto digitado é cifrado localmente com os rotores ativos e enviado ao Raspberry via GET /message/:cipher.
              </Text>
              <TextInput
                autoCapitalize="characters"
                placeholder="Texto claro. Ex: OLA"
                style={styles.input}
                value={message}
                onChangeText={(text) => setMessage(sanitizeMessage(text))}
              />
              <View style={styles.actions}>
                <TouchableOpacity
                  style={[styles.button, styles.primaryButton, isBusy && styles.disabledButton]}
                  disabled={isBusy}
                  onPress={handleSend}
                >
                  <Text style={styles.primaryButtonText}>Cifrar e enviar</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.button, styles.secondaryButton, isBusy && styles.disabledButton]}
                  disabled={isBusy}
                  onPress={() => {
                    void ping();
                  }}
                >
                  <Text style={styles.secondaryButtonText}>Testar ligação</Text>
                </TouchableOpacity>
              </View>
              <MessageHistoryList
                items={sentHistory}
                emptyLabel="Nenhuma mensagem enviada ainda."
              />
            </View>
          ) : (
            <View style={styles.panel}>
              <Text style={styles.sectionTitle}>Aguardar mensagens</Text>
              <Text style={styles.helpText}>
                O app consulta /has-message a cada 4 s. Quando o Raspberry tem uma cifra do Arduino, ela é decifrada localmente.
              </Text>
              <View style={styles.pollStatus}>
                <View style={[styles.pollDot, isPolling && styles.pollDotActive]} />
                <Text style={styles.pollText}>
                  {isPolling ? 'A verificar...' : 'A aguardar mensagens'}
                  {lastPollAt ? ` · ${new Date(lastPollAt).toLocaleTimeString()}` : ''}
                </Text>
              </View>
              <MessageHistoryList
                items={receivedHistory}
                emptyLabel="Nenhuma mensagem recebida ainda."
              />
            </View>
          )}

          {lastError && <Text style={styles.error}>{lastError}</Text>}
        </ScrollView>
      </KeyboardAvoidingView>

      <ConfigModal
        visible={configVisible}
        onClose={() => setConfigVisible(false)}
      />
      <LogsModal visible={logsVisible} onClose={() => setLogsVisible(false)} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#eef2f7',
  },
  flex: {
    flex: 1,
  },
  content: {
    gap: 16,
    padding: 16,
    paddingBottom: 32,
  },
  panel: {
    gap: 12,
  },
  sectionTitle: {
    color: '#0f172a',
    fontSize: 18,
    fontWeight: '800',
  },
  helpText: {
    color: '#64748b',
    lineHeight: 20,
  },
  pollStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#eff6ff',
  },
  pollDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#94a3b8',
  },
  pollDotActive: {
    backgroundColor: '#1d4ed8',
  },
  pollText: {
    flex: 1,
    color: '#334155',
    fontWeight: '600',
    fontSize: 13,
  },
  input: {
    height: 48,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 12,
    color: '#0f172a',
    fontSize: 16,
    letterSpacing: 1,
    backgroundColor: '#ffffff',
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 14,
    borderRadius: 12,
  },
  primaryButton: {
    backgroundColor: '#1d4ed8',
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: '#1d4ed8',
    backgroundColor: '#ffffff',
  },
  disabledButton: {
    opacity: 0.5,
  },
  primaryButtonText: {
    color: '#ffffff',
    fontWeight: '800',
  },
  secondaryButtonText: {
    color: '#1d4ed8',
    fontWeight: '800',
  },
  error: {
    color: '#b3261e',
    fontWeight: '700',
    textAlign: 'center',
  },
});
