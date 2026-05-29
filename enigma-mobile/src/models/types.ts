export type RotorNumber = 1 | 2 | 3 | 4 | 5 | 6;

export type EnigmaMode = 'ENC' | 'DEC';

export type ConnectionState = 'unknown' | 'checking' | 'connected' | 'disconnected';

export type RotorSlot = {
  id: RotorNumber;
  position: number;
};

export type MachineConfig = {
  rotors: RotorSlot[];
  mode: EnigmaMode;
};

export type PingResponse = {
  status: 'ok' | string;
  connectedArduino?: boolean;
};

export type MessageReceipt = {
  status?: string;
  cipher: string;
};

export type HasMessageResponse = {
  cipher: string | null;
};

export type MachineStateResponse = {
  rotors: RotorSlot[];
  connectedArduino?: boolean;
};

export type MessageHistoryItem = {
  id: string;
  plainText: string;
  cipherText: string;
  mode: EnigmaMode;
  direction: 'sent' | 'received';
  createdAt: string;
};

export type HttpLogItem = {
  id: string;
  method: 'GET' | 'POST';
  url: string;
  requestBody?: unknown;
  responseBody?: unknown;
  error?: string;
  status: 'success' | 'error';
  durationMs: number;
  createdAt: string;
};

export type RootStackParamList = {
  Home: undefined;
};
