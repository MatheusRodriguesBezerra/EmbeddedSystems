# Enigma Raspberry

Backend Python (FastAPI) para o Raspberry Pi do projeto Enigma Machine.

## Responsabilidades

- Atuar como **ponte** entre o app mobile (HTTP) e o Arduino (USB Serial).
- Manter a **última configuração de rotores** enviada pelo app mobile, para que o Arduino a possa consultar via `SYNC`.
- Manter a **última cifra recebida do Arduino** (`MESSAGEFROMARDUINO:`) até o app mobile a consumir via `GET /has-message`.
- Encaminhar a cifra recebida do app mobile (`GET /message/:cipher`) para o Arduino como `MESSAGEFROMMOBILE:<cipher>`.

> O Raspberry **não cifra nem decifra**. As máquinas Enigma vivem no Arduino e no app; o backend só transporta payloads cifrados e configurações.

## Rotas HTTP

Todas as rotas devolvem JSON. A base é `http://<IP_DO_RASPBERRY>:8000`.

### `GET /ping`

Teste de conectividade.

```json
{
  "status": "ok",
  "connectedArduino": true
}
```

### `POST /config`

Armazena a configuração atual de rotores enviada pelo app mobile.

Payload:

```json
{
  "rotors": [
    { "id": 1, "position": 5 },
    { "id": 3, "position": 3 },
    { "id": 4, "position": 10 }
  ]
}
```

Resposta:

```json
{
  "rotors": [
    { "id": 1, "position": 5 },
    { "id": 3, "position": 3 },
    { "id": 4, "position": 10 }
  ],
  "connectedArduino": true
}
```

### `GET /message/:cipher`

Recebe uma cifra do app mobile e envia ao Arduino como `MESSAGEFROMMOBILE:<cipher>` pela Serial.

Resposta:

```json
{
  "status": "received",
  "cipher": "XYZ"
}
```

### `GET /has-message`

Consultada pelo app mobile (a cada 4 s no modo DECIFRAR). Devolve a última cifra recebida do Arduino e limpa o buffer, ou `null` se não houver cifra nova.

Resposta com mensagem disponível:

```json
{
  "cipher": "QWE"
}
```

Resposta sem mensagem:

```json
{
  "cipher": null
}
```

## Protocolo serial Arduino ↔ Raspberry

USB Serial @ 115200 baud, linhas terminadas em `\n`.

### Arduino → Raspberry Pi

| Comando                       | Tratamento no Raspberry                                                          |
| ----------------------------- | -------------------------------------------------------------------------------- |
| `MESSAGEFROMARDUINO:<cipher>` | Armazena a cifra como mensagem pendente para o app mobile (`GET /has-message`).  |
| `SYNC`                        | Responde com `POS:<r1,pos>,<r2,pos>,...` (configuração atual armazenada).        |
| `STATUS`                      | Responde com `STATUS:OK`.                                                        |

### Raspberry Pi → Arduino

| Linha enviada                 | Quando                                                                |
| ----------------------------- | --------------------------------------------------------------------- |
| `POS:<r1,pos>,<r2,pos>,...`   | Resposta ao `SYNC`. Se não houver rotores, envia `POS:` (vazio).      |
| `STATUS:OK`                   | Resposta ao `STATUS`.                                                 |
| `MESSAGEFROMMOBILE:<cipher>`  | Sempre que chega `GET /message/:cipher`.                              |

## Arquitetura

```
state/store.py       -> persistência em ficheiro JSON
enigma/models.py     -> modelos pydantic (RotorSlot, Config, etc.)
comm/serial_service  -> leitura/escrita USB Serial em thread dedicada
comm/arduino_handler -> traduz linhas do Arduino em ações de estado/serial
comm/mobile_server   -> FastAPI com as rotas /ping, /config, /message, /has-message
main.py              -> ponto de entrada uvicorn
```

## Execução

No Raspberry Pi OS (Debian) é necessário ambiente virtual (o sistema bloqueia `pip` global):

```bash
cd ~/EmbeddedSystems/enigma-raspberry

sudo apt update
sudo apt install python3-venv python3-full

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py
```

O Arduino deve estar ligado em `/dev/ttyACM0` (ajustável via variável de ambiente `ENIGMA_SERIAL_PORT`).

No app mobile, configure o endereço do Raspberry como `IP_DO_RASPBERRY:8000`.

### Erro `externally-managed-environment`

Significa que correu `pip install` **fora** do venv. Execute `source .venv/bin/activate` e repita `pip install -r requirements.txt`.

## Testes

```bash
source .venv/bin/activate
pytest
```
