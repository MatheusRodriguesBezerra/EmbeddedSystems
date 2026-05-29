import { useEffect, useState } from 'react';
import {
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { MachineConfig } from '../models/types';
import { useConnection } from '../hooks/useConnection';
import { useAppStore } from '../store/useAppStore';
import { isValidRaspberryAddress, isValidRotorConfig } from '../utils/validators';
import { RotorConfigPanel } from './RotorConfigPanel';

type Props = {
  visible: boolean;
  onClose: () => void;
};

export function ConfigModal({ visible, onClose }: Props) {
  const { raspberryAddress, config, lastError, setConfig, setLastError, setRaspberryAddress } =
    useAppStore();
  const { isBusy, syncConfig, ping } = useConnection();
  const [draftAddress, setDraftAddress] = useState(raspberryAddress);
  const [draftConfig, setDraftConfig] = useState<MachineConfig>(config);

  useEffect(() => {
    if (visible) {
      setDraftAddress(raspberryAddress);
      setDraftConfig(config);
    }
  }, [visible, raspberryAddress, config]);

  async function handleSave() {
    if (!isValidRaspberryAddress(draftAddress)) {
      setLastError('Informe o IP ou hostname do Raspberry Pi.');
      return;
    }

    if (!isValidRotorConfig(draftConfig.rotors)) {
      setLastError('Selecione até 4 rotores distintos (R1–R6).');
      return;
    }

    setRaspberryAddress(draftAddress);
    setConfig(draftConfig);
    await syncConfig(draftConfig, draftAddress);
    onClose();
  }

  async function handlePing() {
    setRaspberryAddress(draftAddress);
    await ping(draftAddress);
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <View style={styles.screen}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Configurações</Text>
          <TouchableOpacity onPress={onClose}>
            <Text style={styles.closeText}>Fechar</Text>
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Raspberry Pi</Text>
            <Text style={styles.helpText}>Ex: 192.168.1.100:8000</Text>
            <TextInput
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="IP ou hostname"
              style={styles.input}
              value={draftAddress}
              onChangeText={setDraftAddress}
            />
            <TouchableOpacity
              style={[styles.secondaryButton, isBusy && styles.disabledButton]}
              disabled={isBusy}
              onPress={handlePing}
            >
              <Text style={styles.secondaryButtonText}>Testar /ping</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Rotores</Text>
            <RotorConfigPanel
              rotors={draftConfig.rotors}
              onChange={(rotors) => setDraftConfig((current) => ({ ...current, rotors }))}
            />
          </View>

          {lastError && <Text style={styles.error}>{lastError}</Text>}

          <TouchableOpacity
            style={[styles.primaryButton, isBusy && styles.disabledButton]}
            disabled={isBusy}
            onPress={handleSave}
          >
            <Text style={styles.primaryButtonText}>Salvar e sincronizar</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#eef2f7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  headerTitle: {
    color: '#0f172a',
    fontSize: 20,
    fontWeight: '800',
  },
  closeText: {
    color: '#1d4ed8',
    fontWeight: '800',
  },
  content: {
    gap: 16,
    padding: 16,
    paddingBottom: 32,
  },
  card: {
    gap: 12,
    padding: 16,
    borderRadius: 16,
    backgroundColor: '#ffffff',
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
  input: {
    height: 48,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 12,
    color: '#0f172a',
    fontSize: 16,
  },
  primaryButton: {
    alignItems: 'center',
    paddingVertical: 16,
    borderRadius: 14,
    backgroundColor: '#1d4ed8',
  },
  primaryButtonText: {
    color: '#ffffff',
    fontWeight: '800',
  },
  secondaryButton: {
    alignItems: 'center',
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#1d4ed8',
    borderRadius: 12,
    backgroundColor: '#ffffff',
  },
  secondaryButtonText: {
    color: '#1d4ed8',
    fontWeight: '800',
  },
  disabledButton: {
    opacity: 0.5,
  },
  error: {
    color: '#b3261e',
    fontWeight: '700',
  },
});
