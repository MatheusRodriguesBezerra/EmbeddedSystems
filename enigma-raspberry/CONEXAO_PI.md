# Conexao Arduino + Raspberry Pi + App Mobile

Guia operacional para ligar as tres partes do projeto Enigma Machine.

## Arquitetura

```text
[App Mobile]  <-- Wi-Fi HTTP -->  [Raspberry Pi]  <-- USB Serial -->  [Arduino Mega]
     |                                   |                                   |
  cifra/decifra local                ponte / armazenamento                cifra/decifra local
  (enigma-mobile)                    (enigma-raspberry)                   (enigma-arduino)
```

O Raspberry Pi **nao cifra nem decifra**. As maquinas Enigma vivem no Arduino e no app; o backend so:

1. Mantem a **ultima configuracao de rotores** vinda do app (para o Arduino consultar com `SYNC`).
2. Armazena a **ultima cifra** vinda do Arduino ate o app pedir em `GET /has-message`.
3. **Encaminha** cifras do app para o Arduino via `MESSAGEFROMMOBILE:`.

---

## 1. Hardware: Arduino ao Raspberry Pi

### Cabo

- Arduino Mega **USB** -> porta USB do Raspberry Pi
- O USB do Pi alimenta o Mega

### Firmware

1. Carregue `enigma-arduino/enigma_machine/enigma_machine.ino` no Mega.
2. Serial a **115200 baud**.

### Porta Serial no Pi

```bash
ls -l /dev/ttyACM* /dev/ttyUSB*
```

Porta tipica: `/dev/ttyACM0`.

Permissoes (utilizador `pi`):

```bash
sudo usermod -aG dialout pi
```

Reinicie a sessao SSH ou execute `newgrp dialout`.

Teste rapido:

```bash
python3 -m serial.tools.miniterm /dev/ttyACM0 115200
```

Deve aparecer `ENIGMA: boot`. Ctrl+] para sair.

---

## 2. Backend no Raspberry Pi

```bash
cd enigma-raspberry
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Variaveis opcionais:

```bash
export ENIGMA_SERIAL_PORT=/dev/ttyACM0
export ENIGMA_SERIAL_BAUD=115200
export ENIGMA_SERIAL_ENABLED=1
```

Use `ENIGMA_SERIAL_ENABLED=0` para correr so o HTTP sem Arduino (testes).

Servidor HTTP: `http://IP_DO_PI:8000`.

`GET /ping` deve responder `{"status": "ok", "connectedArduino": true}` (ou `false` se o Arduino nao estiver ligado).

---

## 3. Protocolo Serial (Arduino <-> Pi)

Linhas terminadas em `\n`, ASCII, 115200 baud.

### Arduino -> Pi

| Comando                       | Quando                                              |
| ----------------------------- | --------------------------------------------------- |
| `SYNC`                        | Tecla `SYNC` no Arduino                             |
| `STATUS`                      | Pedido de keepalive / verificacao                   |
| `MESSAGEFROMARDUINO:<cipher>` | Tecla `SEND` em modo CIFRAR (apos `LOCK`)           |

### Pi -> Arduino

| Linha enviada                | Quando                                                                  |
| ---------------------------- | ----------------------------------------------------------------------- |
| `POS:<r1,p1,r2,p2,...>`      | Resposta ao `SYNC` (vazio = `POS:`)                                     |
| `STATUS:OK`                  | Resposta ao `STATUS`                                                    |
| `MESSAGEFROMMOBILE:<cipher>` | Sempre que chega `GET /message/:cipher` do app mobile                    |
| `ACK:<cipher>`               | Confirmacao de `MESSAGEFROMARDUINO:` aceite                              |
| `ERR:<codigo>`               | Erro (ex.: `ERR:PAYLOAD_VAZIO`)                                          |

---

## 4. API HTTP (Pi <-> App Mobile)

| Rota                     | Funcao                                                                  |
| ------------------------ | ----------------------------------------------------------------------- |
| `GET /ping`              | Estado do backend e do Arduino                                          |
| `POST /config`           | App envia a configuracao atual `{ rotors: [{id, position}, ...] }`      |
| `GET /message/{cipher}`  | App envia cifra; Pi reenvia ao Arduino via `MESSAGEFROMMOBILE:`         |
| `GET /has-message`       | App faz polling a cada 4 s; devolve `{cipher: "..."}` ou `{cipher: null}` |

---

## 5. Fluxos completos

### A) App envia mensagem para a maquina fisica

**Pre-condicao:** App e Arduino com a mesma configuracao de rotores.

1. App esta em modo CIFRAR. Utilizador digita "OLA".
2. App cifra localmente -> ex.: "PKN".
3. App chama `GET http://PI:8000/message/PKN`.
4. Pi envia ao Arduino: `MESSAGEFROMMOBILE:PKN`.
5. Arduino (em DECIFRAR, com LOCK ativo) decifra, mostra a cifra na linha 1 do LCD e o claro na linha 2; pisca L1-L5 a cada letra (1200 ms).

### B) Maquina fisica envia mensagem para o app

**Pre-condicao:** App em DECIFRAR, Arduino em CIFRAR com mesma configuracao.

1. No Arduino: configura rotores, pressiona LOCK, digita "OLA".
2. Pressiona SEND -> Arduino envia `MESSAGEFROMARDUINO:<cipher>`.
3. Pi armazena o cipher como pendente e responde `ACK:<cipher>`.
4. App faz `GET /has-message` (polling 4 s). Pi devolve `{"cipher": "<cipher>"}` e limpa o buffer.
5. App decifra localmente e mostra o claro ao utilizador.

### C) Sincronizar configuracao

1. No app, escolher os rotores -> `POST /config` (`{"rotors": [{"id": 1, "position": 5}, ...]}`).
2. No Arduino, pressionar `SYNC` -> Pi responde `POS:1,5,...`.

---

## 6. App mobile (`enigma-mobile`)

Configure o IP do Pi nas configuracoes (ex.: `192.168.1.50:8000`).

```typescript
GET /ping
POST /config  { rotors: [...] }

// App envia (modo CIFRAR)
const cipher = enigma.encrypt(plain);
GET /message/${cipher}

// App recebe (modo DECIFRAR, polling 4 s)
GET /has-message
// -> { cipher: "..." | null }
const plain = enigma.decrypt(response.cipher);
```

---

## 7. Ordem de arranque

1. Ligar Raspberry Pi (Wi-Fi ativo).
2. Ligar Arduino ao Pi por USB.
3. `python main.py` no Pi.
4. Confirmar `/ping` com `connectedArduino: true`.
5. No app, configurar IP e rotores -> `POST /config`.
6. No Arduino, pressionar `SYNC` para receber a configuracao.
7. Pressionar `LOCK` no Arduino e comecar a comunicar.
