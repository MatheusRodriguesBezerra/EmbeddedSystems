# Conexao Arduino + Raspberry Pi + App Mobile

Este guia liga as tres partes do projeto Enigma Machine.

## Arquitetura

```text
[App Mobile]  <-- Wi-Fi HTTP -->  [Raspberry Pi]  <-- USB Serial -->  [Arduino Mega]
     |                                   |
  cifra/decifra local              estado central + ponte
  (enigmaMachine.ts)               (enigma-raspberry)
                                         |
                                   Arduino cifra/decifra
                                   localmente (LCD/LEDs)
```

O Raspberry Pi **nao re-cifra** mensagens ja cifradas no Arduino ou no app. Ele:

1. Mantem o **estado** (rotores, turno, modo).
2. **Encaminha** payloads entre Serial e HTTP.
3. **Alinha posicoes** dos rotores processando o payload (Enigma simetrica).

---

## 1. Hardware: Arduino ao Raspberry Pi

### Cabo

- Arduino Mega **USB** -> porta USB do Raspberry Pi 3 B+
- Alimentacao: USB do Pi alimenta o Mega (consumo moderado)

### Firmware

1. Carregue `enigma-arduino/enigma_machine/enigma_machine.ino` no Mega.
2. Serial a **115200 baud** (igual ao `config.h` do Arduino e ao Pi).

### Porta Serial no Pi

Com o Arduino ligado:

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

### Instalacao

```bash
cd enigma-raspberry
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Variaveis (opcional)

```bash
export ENIGMA_SERIAL_PORT=/dev/ttyACM0
export ENIGMA_SERIAL_BAUD=115200
export ENIGMA_SERIAL_ENABLED=1
```

Use `ENIGMA_SERIAL_ENABLED=0` para correr so HTTP sem Arduino.

### Executar

```bash
python main.py
```

Servidor HTTP: `http://IP_DO_PI:8000`

`GET /ping` deve responder:

```json
{ "status": "ok", "connectedArduino": true }
```

---

## 3. Protocolo Serial (Arduino <-> Pi)

### Arduino -> Pi

| Comando | Quando |
| --- | --- |
| `SYNC` | Tecla RESET/SYNC |
| `SEND:<cipher>` | Tecla SEND (modo cifrar) |
| `MODE:ENC` / `MODE:DEC` | Tecla MODE |

### Pi -> Arduino

| Resposta | Significado |
| --- | --- |
| `POS:r1,r2,r3` | Posicoes dos rotores (sync) |
| `IN:<cipher>` | Payload cifrado para decifrar no LCD |
| `ACK:<messageId>` | SEND aceite |
| `ERR:<codigo>` | Erro (ex.: `NOT_SENDING`) |

---

## 4. API HTTP (Pi <-> App Mobile)

| Rota | Funcao |
| --- | --- |
| `GET /ping` | Conectividade + Arduino ligado |
| `GET /state` | Estado completo + `pending` |
| `POST /config` | Sincronizar rotores, posicoes, modo, **role** |
| `GET /message/{payload}` | App envia payload **ja cifrado** (app em SENDING) |
| `GET /pending` | App recebe payload cifrado da maquina fisica |
| `POST /outgoing/{texto}` | Pi cifra texto (teste sem Arduino) |

### Turno half-duplex (`role`)

| Role no Pi | Quem pode enviar |
| --- | --- |
| `SENDING` | Maquina fisica (Arduino SEND) |
| `RECEIVING` | App mobile (`GET /message/...`) |

Apos cada mensagem processada, o role **alterna** automaticamente.

---

## 5. Fluxos completos

### A) App envia mensagem para a maquina fisica

**Pre-condicao:** Pi em `RECEIVING`, app em `SENDING`, mesmas posicoes (ex.: `0,0,0`).

1. App cifra `"OLA"` localmente -> ex.: `"PKN"`
2. App chama `GET http://PI:8000/message/PKN`
3. Pi decifra (alinha rotores), role passa a `SENDING`
4. Pi envia ao Arduino: `IN:PKN`
5. Arduino (modo decifrar) mostra cifrado na linha 1 e claro na linha 2

### B) Maquina fisica envia mensagem para o app

**Pre-condicao:** Pi em `SENDING`, app em `RECEIVING`.

1. No Arduino: MODE -> cifrar, digitar `OLA`, SEND
2. Arduino envia `SEND:<cipher>` ao Pi
3. Pi responde `ACK:<id>`, guarda payload, role passa a `RECEIVING`
4. App faz polling: `GET http://PI:8000/pending`
5. App decifra localmente o `payload`

### C) Sincronizar antes de comecar

**POST /config** (app ou curl):

```json
{
  "order": ["I", "II", "III"],
  "positions": [0, 0, 0],
  "mode": "DEC",
  "role": "SENDING"
}
```

**No Arduino:** tecla RESET/SYNC -> Pi responde `POS:0,0,0`

Para a maquina fisica enviar primeiro: Pi `role: "SENDING"`, app `role: "RECEIVING"`.

Para o app enviar primeiro: Pi `role: "RECEIVING"`, app `role: "SENDING"`.

---

## 6. App mobile (`enigma-mobile`)

Configure o IP do Pi na tela Config (ex.: `192.168.1.50:8000`).

```typescript
GET /ping
POST /config  { order, positions, mode, role }

// App envia (SENDING)
const cipher = enigma.encrypt(plain);
GET /message/${cipher}

// App recebe da maquina fisica (RECEIVING)
GET /pending?consume=true
const plain = enigma.decrypt(response.payload);
```

Em `RECEIVING`, faca polling periodico em `GET /pending` ou consulte `GET /state` (`pending.available`).

---

## 7. Ordem de arranque

1. Ligar Raspberry Pi (Wi-Fi ativo)
2. Ligar Arduino ao Pi por USB
3. `python main.py` no Pi
4. Confirmar `/ping` com `connectedArduino: true`
5. `POST /config` com roles alinhados
6. RESET/SYNC no Arduino
7. Abrir app mobile na mesma rede Wi-Fi
