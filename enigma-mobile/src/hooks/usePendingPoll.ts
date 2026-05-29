import { useCallback, useEffect, useRef, useState } from 'react';

import { EnigmaHttpService } from '../services/httpService';
import { processEnigmaMessage } from '../services/enigmaMachine';
import { useAppStore } from '../store/useAppStore';
import { MOBILE_API, POLL_INTERVAL_MS } from '../services/apiProtocol';
import { isValidRaspberryAddress, normalizeBaseUrl, sanitizeMessage } from '../utils/validators';

type Options = {
  enabled: boolean;
  onMessageReceived?: () => void;
};

/**
 * Hook que faz polling em GET /has-message a cada POLL_INTERVAL_MS (4 s).
 * Quando o Raspberry devolve uma cifra, decifra localmente e atualiza o estado.
 */
export function usePendingPoll({ enabled, onMessageReceived }: Options) {
  const [isPolling, setIsPolling] = useState(false);
  const [lastPollAt, setLastPollAt] = useState<string | undefined>();
  const {
    raspberryAddress,
    config,
    setConfig,
    setConnection,
    setLastSyncAt,
    addReceivedMessage,
    addHttpLog,
  } = useAppStore();

  const configRef = useRef(config);
  configRef.current = config;

  const applyReceivedCipher = useCallback(
    (rawCipher: string) => {
      const currentConfig = configRef.current;
      const cipher = sanitizeMessage(rawCipher);
      if (!cipher || currentConfig.rotors.length === 0) {
        return false;
      }

      const decrypted = processEnigmaMessage(cipher, currentConfig);
      addReceivedMessage({ plainText: decrypted.output, cipherText: cipher });
      setConfig({
        ...currentConfig,
        rotors: decrypted.rotors,
      });
      setLastSyncAt(new Date().toISOString());
      setConnection('connected');
      return true;
    },
    [addReceivedMessage, setConfig, setConnection, setLastSyncAt],
  );

  useEffect(() => {
    if (!enabled || !isValidRaspberryAddress(raspberryAddress)) {
      setIsPolling(false);
      return;
    }

    let cancelled = false;
    let inFlight = false;

    async function pollOnce() {
      if (cancelled || inFlight) {
        return;
      }

      inFlight = true;
      setIsPolling(true);
      const startedAt = Date.now();
      const url = `${normalizeBaseUrl(raspberryAddress)}${MOBILE_API.hasMessage}`;

      try {
        const response = await new EnigmaHttpService(raspberryAddress).fetchHasMessage();
        setLastPollAt(new Date().toISOString());
        setConnection('connected');

        if (response.cipher) {
          const received = applyReceivedCipher(response.cipher);
          if (received) {
            addHttpLog({
              method: 'GET',
              url,
              status: 'success',
              responseBody: response,
              durationMs: Date.now() - startedAt,
            });
            onMessageReceived?.();
          }
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Falha ao consultar /has-message.';
        setConnection('disconnected');
        addHttpLog({
          method: 'GET',
          url,
          status: 'error',
          error: message,
          durationMs: Date.now() - startedAt,
        });
      } finally {
        inFlight = false;
        if (!cancelled) {
          setIsPolling(false);
        }
      }
    }

    void pollOnce();
    const intervalId = setInterval(() => {
      void pollOnce();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
      setIsPolling(false);
    };
  }, [
    enabled,
    raspberryAddress,
    applyReceivedCipher,
    addHttpLog,
    onMessageReceived,
    setConnection,
  ]);

  return { isPolling, lastPollAt };
}
