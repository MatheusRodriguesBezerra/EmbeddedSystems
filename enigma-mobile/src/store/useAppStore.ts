import { create } from 'zustand';

import {
  ConnectionState,
  EnigmaMode,
  HttpLogItem,
  MachineConfig,
  MessageHistoryItem,
} from '../models/types';

type AppStore = {
  raspberryAddress: string;
  connection: ConnectionState;
  connectedArduino: boolean;
  config: MachineConfig;
  lastSentMessage: string;
  receivedMessage: string;
  lastCipherPayload: string;
  history: MessageHistoryItem[];
  httpLogs: HttpLogItem[];
  lastError?: string;
  lastSyncAt?: string;
  setRaspberryAddress: (value: string) => void;
  setConnection: (value: ConnectionState) => void;
  setConnectedArduino: (value: boolean) => void;
  setConfig: (value: MachineConfig) => void;
  setMode: (value: EnigmaMode) => void;
  setLastError: (value?: string) => void;
  setLastSyncAt: (value: string) => void;
  addSentMessage: (value: { plainText: string; cipherText: string }) => void;
  addReceivedMessage: (value: { plainText: string; cipherText: string }) => void;
  addHttpLog: (value: Omit<HttpLogItem, 'id' | 'createdAt'>) => void;
  clearHttpLogs: () => void;
};

export const DEFAULT_CONFIG: MachineConfig = {
  rotors: [],
  mode: 'ENC',
};

export const useAppStore = create<AppStore>((set) => ({
  raspberryAddress: '192.168.1.100:8000',
  connection: 'unknown',
  connectedArduino: false,
  config: DEFAULT_CONFIG,
  lastSentMessage: '',
  receivedMessage: '',
  lastCipherPayload: '',
  history: [],
  httpLogs: [],
  lastError: undefined,
  lastSyncAt: undefined,
  setRaspberryAddress: (raspberryAddress) => set({ raspberryAddress }),
  setConnection: (connection) => set({ connection }),
  setConnectedArduino: (connectedArduino) => set({ connectedArduino }),
  setConfig: (config) => set({ config }),
  setMode: (mode) =>
    set((state) => ({
      config: {
        ...state.config,
        mode,
      },
    })),
  setLastError: (lastError) => set({ lastError }),
  setLastSyncAt: (lastSyncAt) => set({ lastSyncAt }),
  addSentMessage: (message) =>
    set((state) => ({
      lastSentMessage: message.plainText,
      lastCipherPayload: message.cipherText,
      history: [
        {
          id: `${Date.now()}-${state.history.length}`,
          plainText: message.plainText,
          cipherText: message.cipherText,
          mode: state.config.mode,
          direction: 'sent' as const,
          createdAt: new Date().toISOString(),
        },
        ...state.history,
      ].slice(0, 20),
    })),
  addReceivedMessage: (message) =>
    set((state) => ({
      receivedMessage: message.plainText,
      lastCipherPayload: message.cipherText,
      history: [
        {
          id: `${Date.now()}-${state.history.length}`,
          plainText: message.plainText,
          cipherText: message.cipherText,
          mode: state.config.mode,
          direction: 'received' as const,
          createdAt: new Date().toISOString(),
        },
        ...state.history,
      ].slice(0, 20),
    })),
  addHttpLog: (log) =>
    set((state) => ({
      httpLogs: [
        {
          ...log,
          id: `${Date.now()}-${state.httpLogs.length}`,
          createdAt: new Date().toISOString(),
        },
        ...state.httpLogs,
      ].slice(0, 100),
    })),
  clearHttpLogs: () => set({ httpLogs: [] }),
}));
