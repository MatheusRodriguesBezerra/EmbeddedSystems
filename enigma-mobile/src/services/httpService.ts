import {
  HasMessageResponse,
  MachineConfig,
  MachineStateResponse,
  MessageReceipt,
  PingResponse,
} from '../models/types';
import { buildConfigPayload, MOBILE_API } from './apiProtocol';
import { normalizeBaseUrl } from '../utils/validators';

const REQUEST_TIMEOUT_MS = 5000;

async function requestJson<T>(url: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const body = (await response.json()) as { detail?: string | unknown };
        if (typeof body.detail === 'string') {
          detail = body.detail;
        } else if (body.detail) {
          detail = JSON.stringify(body.detail);
        }
      } catch {
        // corpo nao-JSON
      }
      throw new Error(detail);
    }

    return (await response.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

export class EnigmaHttpService {
  private readonly baseUrl: string;

  constructor(raspberryAddress: string) {
    this.baseUrl = normalizeBaseUrl(raspberryAddress);
  }

  ping() {
    return requestJson<PingResponse>(`${this.baseUrl}${MOBILE_API.ping}`);
  }

  sendCipher(cipher: string) {
    return requestJson<MessageReceipt>(`${this.baseUrl}${MOBILE_API.message(cipher)}`);
  }

  updateConfig(config: MachineConfig) {
    return requestJson<MachineStateResponse>(`${this.baseUrl}${MOBILE_API.config}`, {
      method: 'POST',
      body: JSON.stringify(buildConfigPayload(config)),
    });
  }

  fetchHasMessage() {
    return requestJson<HasMessageResponse>(`${this.baseUrl}${MOBILE_API.hasMessage}`);
  }
}
