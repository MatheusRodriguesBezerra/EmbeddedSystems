import { useState } from 'react';

import { MachineConfig } from '../models/types';
import { EnigmaHttpService } from '../services/httpService';
import { processEnigmaMessage } from '../services/enigmaMachine';
import { useAppStore } from '../store/useAppStore';
import { MOBILE_API, buildConfigPayload, isPingOk } from '../services/apiProtocol';
import {
  isValidRaspberryAddress,
  normalizeBaseUrl,
  sanitizeMessage,
} from '../utils/validators';

export function useConnection() {
  const [isBusy, setIsBusy] = useState(false);
  const {
    raspberryAddress,
    config,
    setConnection,
    setConnectedArduino,
    setConfig,
    setLastError,
    setLastSyncAt,
    addSentMessage,
    addReceivedMessage,
    addHttpLog,
  } = useAppStore();

  function makeService(address = raspberryAddress) {
    return new EnigmaHttpService(address);
  }

  async function ping(address = raspberryAddress) {
    const startedAt = Date.now();
    const url = isValidRaspberryAddress(address)
      ? `${normalizeBaseUrl(address)}${MOBILE_API.ping}`
      : `${address}${MOBILE_API.ping}`;

    if (!isValidRaspberryAddress(address)) {
      setConnection('disconnected');
      setLastError('Endereco do Raspberry Pi invalido.');
      addHttpLog({
        method: 'GET',
        url,
        status: 'error',
        error: 'Endereco do Raspberry Pi invalido.',
        durationMs: Date.now() - startedAt,
      });
      return false;
    }

    setIsBusy(true);
    setConnection('checking');
    setLastError(undefined);

    try {
      const response = await makeService(address).ping();
      const connected = isPingOk(response);

      setConnection(connected ? 'connected' : 'disconnected');
      setConnectedArduino(Boolean(response.connectedArduino));
      setLastSyncAt(new Date().toISOString());
      addHttpLog({
        method: 'GET',
        url,
        status: connected ? 'success' : 'error',
        responseBody: response,
        durationMs: Date.now() - startedAt,
      });
      return connected;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Falha ao comunicar.';
      setConnection('disconnected');
      setLastError(message);
      addHttpLog({
        method: 'GET',
        url,
        status: 'error',
        error: message,
        durationMs: Date.now() - startedAt,
      });
      return false;
    } finally {
      setIsBusy(false);
    }
  }

  async function sendMessage(rawMessage: string): Promise<boolean> {
    const message = sanitizeMessage(rawMessage);
    const startedAt = Date.now();

    if (!message) {
      setLastError('Digite uma mensagem com letras de A a Z.');
      return false;
    }

    if (config.rotors.length === 0) {
      setLastError('Configure pelo menos um rotor antes de enviar.');
      return false;
    }

    const encrypted = processEnigmaMessage(message, config);
    const url = `${normalizeBaseUrl(raspberryAddress)}${MOBILE_API.message(encrypted.output)}`;

    setIsBusy(true);
    setLastError(undefined);

    try {
      const response = await makeService().sendCipher(encrypted.output);
      const cipherText = sanitizeMessage(response.cipher ?? encrypted.output);

      if (!cipherText) {
        throw new Error('Raspberry Pi nao confirmou o payload cifrado.');
      }

      addSentMessage({
        plainText: message,
        cipherText,
      });
      setConfig({
        rotors: encrypted.rotors,
        mode: config.mode,
      });
      setConnection('connected');
      setLastSyncAt(new Date().toISOString());
      addHttpLog({
        method: 'GET',
        url,
        status: 'success',
        responseBody: response,
        durationMs: Date.now() - startedAt,
      });
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao enviar mensagem.';
      setConnection('disconnected');
      setLastError(errorMessage);
      addHttpLog({
        method: 'GET',
        url,
        status: 'error',
        error: errorMessage,
        durationMs: Date.now() - startedAt,
      });
      return false;
    } finally {
      setIsBusy(false);
    }
  }

  function applyReceivedCipher(rawCipher: string): boolean {
    const cipher = sanitizeMessage(rawCipher);

    if (!cipher) {
      setLastError('Payload cifrado invalido.');
      return false;
    }

    if (config.rotors.length === 0) {
      setLastError('Configure os rotores antes de receber.');
      return false;
    }

    const decrypted = processEnigmaMessage(cipher, config);
    addReceivedMessage({ plainText: decrypted.output, cipherText: cipher });
    setConfig({
      ...config,
      rotors: decrypted.rotors,
    });
    setLastError(undefined);
    setLastSyncAt(new Date().toISOString());
    return true;
  }

  async function syncConfig(
    configOverride?: MachineConfig,
    addressOverride?: string,
    options?: { silent?: boolean },
  ) {
    const silent = options?.silent ?? false;
    const startedAt = Date.now();
    const targetAddress = addressOverride ?? raspberryAddress;
    const localConfig = configOverride ?? config;
    const configPayload = buildConfigPayload(localConfig);
    const url = `${normalizeBaseUrl(targetAddress)}${MOBILE_API.config}`;

    if (!silent) {
      setIsBusy(true);
      setLastError(undefined);
    }

    try {
      const response = await makeService(addressOverride).updateConfig(localConfig);
      setConfig({
        rotors: response.rotors,
        mode: localConfig.mode,
      });
      setConnectedArduino(Boolean(response.connectedArduino));
      setConnection('connected');
      setLastSyncAt(new Date().toISOString());
      if (!silent) {
        addHttpLog({
          method: 'POST',
          url,
          requestBody: configPayload,
          responseBody: response,
          status: 'success',
          durationMs: Date.now() - startedAt,
        });
      }
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro ao sincronizar.';
      setConnection('disconnected');
      if (!silent) {
        setLastError(errorMessage);
        addHttpLog({
          method: 'POST',
          url,
          requestBody: configPayload,
          status: 'error',
          error: errorMessage,
          durationMs: Date.now() - startedAt,
        });
      }
      return false;
    } finally {
      if (!silent) {
        setIsBusy(false);
      }
    }
  }

  return {
    isBusy,
    ping,
    sendMessage,
    applyReceivedCipher,
    syncConfig,
  };
}
