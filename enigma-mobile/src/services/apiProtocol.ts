import { MachineConfig, PingResponse } from '../models/types';

export const MOBILE_API = {
  ping: '/ping',
  config: '/config',
  message: (cipher: string) => `/message/${encodeURIComponent(cipher)}`,
  hasMessage: '/has-message',
};

export const POLL_INTERVAL_MS = 4000;

export function isPingOk(response: PingResponse) {
  return typeof response.status === 'string' && response.status.toLowerCase() === 'ok';
}

export function buildConfigPayload(config: MachineConfig) {
  return { rotors: config.rotors };
}
